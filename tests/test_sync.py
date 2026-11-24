from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Dict, List
import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_sync_receiver_module():
    for mod_name in ("python.sync_receiver", "python.sync_reciever"):
        try:
            return importlib.import_module(mod_name)
        except ModuleNotFoundError:
            continue
    raise ModuleNotFoundError("Could not find python/sync_receiver.py or python/sync_reciever.py")


def _load_logger_module():
    return importlib.import_module("python.logger")


def _make_records(count: int = 1000, device_id: str = "coldchain-01") -> List[Dict[str, Any]]:
    base_ts = 1700000000
    rows: List[Dict[str, Any]] = []
    for i in range(1, count + 1):
        rows.append(
            {
                "device_id": device_id,
                "seq": i,
                "timestamp": base_ts + i,
                "t0_air_c": round(4.5 + (i % 5) * 0.2, 2),
                "t1_pay_c": round(4.2 + (i % 4) * 0.2, 2),
                "t2_out_c": 22.5,
                "lid": "CLOSED",
                "status": "OK",
            }
        )
    return rows


def test_sync_1000_records_batches_retries_and_dedup():
    sync_mod = _load_sync_receiver_module()
    app = sync_mod.create_app()
    client = app.test_client()

    assert client.post("/reset").status_code == 200

    records = _make_records(count=1000, device_id="coldchain-01")
    batch_size = 50
    batches = [records[i : i + batch_size] for i in range(0, len(records), batch_size)]
    assert len(batches) == 20

    # Simulate transient drop/timeout on batch 3 and batch 11, with retries
    drop_once_batches = {2, 10}
    dropped_already: set[int] = set()

    for idx, batch in enumerate(batches):
        while True:
            if idx in drop_once_batches and idx not in dropped_already:
                dropped_already.add(idx)
                # Simulated timeout/drop -> retry same batch
                continue

            resp = client.post("/sync", json={"device_id": "coldchain-01", "records": batch})
            assert resp.status_code == 200
            break

    # Resend overlapping batches (batches 0 and 1) to simulate duplicate delivery
    for dup_batch in batches[:2]:
        resp = client.post("/sync", json={"device_id": "coldchain-01", "records": dup_batch})
        assert resp.status_code == 200

    stats_resp = client.get("/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json

    assert stats["unique_count"] == 1000
    assert stats["missing_count"] == 0
    assert stats["duplicate_count"] > 0


def test_logger_sequence_persistence_and_hash(tmp_path: Path):
    logger_mod = _load_logger_module()
    CSVLogger = logger_mod.CSVLogger

    log_file = tmp_path / "log.csv"
    hash_file = tmp_path / "hashes.txt"

    logger1 = CSVLogger(log_path=log_file, hash_path=hash_file)
    for _ in range(5):
        logger1.log_record({"t0_air_c": 5.0, "t1_pay_c": 4.9, "t2_out_c": 23.0, "lid": "CLOSED", "status": "OK"})

    # Restart logger and log 3 more rows -> seq should continue 6, 7, 8
    logger2 = CSVLogger(log_path=log_file, hash_path=hash_file)
    assert logger2.next_seq == 6
    for _ in range(3):
        logger2.log_record({"t0_air_c": 5.1, "t1_pay_c": 5.0, "t2_out_c": 23.1, "lid": "CLOSED", "status": "OK"})

    digest = logger2.write_hash_entry(epoch=1700000100)
    assert len(digest) == 64

    rows = logger2.read_records()
    assert [r["seq"] for r in rows] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert logger2.find_sequence_gaps() == []
    assert hash_file.exists()
    assert "1700000100,log.csv," in hash_file.read_text(encoding="utf-8")