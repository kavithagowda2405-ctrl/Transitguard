from __future__ import annotations

import csv
import hashlib
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def get_repo_root() -> Path:
    """Resolve Transitguard/ root even if run from another folder."""
    return Path(__file__).resolve().parent.parent


def default_log_path() -> Path:
    return get_repo_root() / "data" / "log.csv"


def default_hash_path() -> Path:
    return get_repo_root() / "data" / "hashes.txt"


DEFAULT_FIELDNAMES: List[str] = [
    "seq",
    "timestamp",
    "t0_air_c",
    "t1_pay_c",
    "t2_out_c",
    "lid",
    "status",
]


class CSVLogger:
    def __init__(
        self,
        log_path: str | os.PathLike[str] | None = None,
        hash_path: str | os.PathLike[str] | None = None,
        fieldnames: Optional[List[str]] = None,
        hash_interval_sec: int = 3600,
    ) -> None:
        self.log_path: Path = Path(log_path) if log_path is not None else default_log_path()
        self.hash_path: Path = Path(hash_path) if hash_path is not None else default_hash_path()
        self.fieldnames: List[str] = list(fieldnames) if fieldnames else list(DEFAULT_FIELDNAMES)
        if "seq" not in self.fieldnames:
            self.fieldnames.insert(0, "seq")

        self.hash_interval_sec: int = hash_interval_sec
        self._last_hash_epoch: float = 0.0

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.hash_path.parent.mkdir(parents=True, exist_ok=True)

        self._next_seq: int = self._read_next_seq()

    def _read_next_seq(self) -> int:
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            return 1

        max_seq = 0
        with self.log_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_seq = (row.get("seq") or "").strip()
                if raw_seq.isdigit():
                    val = int(raw_seq)
                    if val > max_seq:
                        max_seq = val
        return max_seq + 1

    @property
    def next_seq(self) -> int:
        return self._next_seq

    def log_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        file_exists = self.log_path.exists() and self.log_path.stat().st_size > 0

        row_data = dict(record)
        if "seq" not in row_data or row_data["seq"] is None or str(row_data["seq"]).strip() == "":
            seq_val = self._next_seq
            self._next_seq += 1
        else:
            seq_val = int(row_data["seq"])
            if seq_val >= self._next_seq:
                self._next_seq = seq_val + 1

        row_data["seq"] = seq_val
        if "timestamp" not in row_data or row_data["timestamp"] is None:
            row_data["timestamp"] = int(time.time())

        all_fields = list(self.fieldnames)
        for k in row_data.keys():
            if k not in all_fields:
                all_fields.append(k)

        if not file_exists:
            self.fieldnames = all_fields
            with self.log_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerow(row_data)
        else:
            with self.log_path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames, extrasaction="ignore")
                writer.writerow(row_data)

        return row_data

    def log_many(self, records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.log_record(rec) for rec in records]

    def compute_sha256(self) -> str:
        h = hashlib.sha256()
        if not self.log_path.exists():
            return h.hexdigest()
        with self.log_path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def write_hash_entry(self, epoch: Optional[int] = None) -> str:
        ts_epoch = int(time.time()) if epoch is None else int(epoch)
        digest = self.compute_sha256()
        line = f"{ts_epoch},{self.log_path.name},{digest}\n"
        with self.hash_path.open("a", encoding="utf-8") as f:
            f.write(line)
        self._last_hash_epoch = float(ts_epoch)
        return digest

    def maybe_write_hourly_hash(self, force: bool = False, now_epoch: Optional[float] = None) -> Optional[str]:
        current = time.time() if now_epoch is None else float(now_epoch)
        if force or self._last_hash_epoch == 0.0 or (current - self._last_hash_epoch) >= self.hash_interval_sec:
            return self.write_hash_entry(epoch=int(current))
        return None

    def find_sequence_gaps(self) -> List[int]:
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            return []

        seen: set[int] = set()
        max_seq = 0
        with self.log_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_seq = (row.get("seq") or "").strip()
                if raw_seq.isdigit():
                    val = int(raw_seq)
                    seen.add(val)
                    if val > max_seq:
                        max_seq = val

        return [s for s in range(1, max_seq + 1) if s not in seen]

    def read_records(self) -> List[Dict[str, Any]]:
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            return []
        rows: List[Dict[str, Any]] = []
        with self.log_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                item = dict(row)
                if "seq" in item and str(item["seq"]).strip().isdigit():
                    item["seq"] = int(item["seq"])
                rows.append(item)
        return rows


if __name__ == "__main__":
    logger = CSVLogger()
    rec = logger.log_record({"t0_air_c": 5.2, "t1_pay_c": 5.1, "t2_out_c": 24.0, "lid": "CLOSED", "status": "OK"})
    logger.maybe_write_hourly_hash(force=True)
    print("Logged:", rec)