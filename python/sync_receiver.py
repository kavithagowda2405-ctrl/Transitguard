from __future__ import annotations

import threading
from typing import Any, Dict, List, Set, Tuple
from flask import Flask, jsonify, request


class SyncStore:
    """In-memory deduplicated receiver store keyed by (device_id, seq)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self._seen_keys: Set[Tuple[str, int]] = set()
            self._records: Dict[Tuple[str, int], Dict[str, Any]] = {}
            self._seqs_by_device: Dict[str, Set[int]] = {}
            self.total_received: int = 0
            self.duplicate_count: int = 0

    def ingest(self, device_id: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        accepted = 0
        duplicates = 0

        with self._lock:
            dev_seqs = self._seqs_by_device.setdefault(device_id, set())

            for rec in records:
                if "seq" not in rec:
                    continue
                seq = int(rec["seq"])
                key = (device_id, seq)
                self.total_received += 1

                if key in self._seen_keys:
                    self.duplicate_count += 1
                    duplicates += 1
                else:
                    self._seen_keys.add(key)
                    stored = dict(rec)
                    stored["device_id"] = device_id
                    stored["seq"] = seq
                    self._records[key] = stored
                    dev_seqs.add(seq)
                    accepted += 1

        return {
            "status": "ok",
            "device_id": device_id,
            "accepted": accepted,
            "duplicates": duplicates,
        }

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            missing_total = 0
            missing_by_device: Dict[str, List[int]] = {}

            for dev_id, seqs in self._seqs_by_device.items():
                if not seqs:
                    missing_by_device[dev_id] = []
                    continue
                max_seq = max(seqs)
                missing = [s for s in range(1, max_seq + 1) if s not in seqs]
                missing_by_device[dev_id] = missing
                missing_total += len(missing)

            return {
                "unique_count": len(self._seen_keys),
                "duplicate_count": self.duplicate_count,
                "total_received": self.total_received,
                "missing_count": missing_total,
                "missing_by_device": missing_by_device,
            }


def create_app(store: SyncStore | None = None) -> Flask:
    app = Flask(__name__)
    sync_store = store or SyncStore()
    app.config["SYNC_STORE"] = sync_store

    @app.post("/sync")
    def sync_endpoint():
        payload = request.get_json(silent=True) or {}
        device_id = str(payload.get("device_id", "default-device"))
        records = payload.get("records")

        if not isinstance(records, list):
            return jsonify({"error": "records must be a list"}), 400

        result = sync_store.ingest(device_id=device_id, records=records)
        return jsonify(result), 200

    @app.get("/stats")
    def stats_endpoint():
        return jsonify(sync_store.stats()), 200

    @app.post("/reset")
    def reset_endpoint():
        sync_store.reset()
        return jsonify({"status": "reset"}), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)