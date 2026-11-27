"""M4: one summary row per run in data/ (lid events, risk status, alert episodes, sequence check).
Usage: python python/summary_all.py     -> prints a table and writes docs/m4_summary.csv"""
import glob
import os
import sys
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from log_tools import load_log, load_events, check_sequence
from events import door_events, door_aware_alerts, alert_episodes, crosscheck_door
from risk import risk_status

ROOT = os.path.join(os.path.dirname(__file__), "..")


def main():
    rows = []
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "log_*_*.csv"))):
        name = os.path.basename(p)[4:-4]
        df = load_log(p)
        r = risk_status(df)
        ep = alert_episodes(door_aware_alerts(df), df["time_s"].values)
        ev_path = os.path.join(ROOT, "data", f"events_{name}.csv")
        cross = crosscheck_door(df, load_events(ev_path)) if os.path.exists(ev_path) else {"matched": None}
        seq = check_sequence(df["seq"])
        rows.append({"run": name, "lid_openings": len(door_events(df)), "lid_open_s": r["door_open_s"],
                     "degree_minutes": round(r["degree_minutes"], 1), "peak_dev_C": round(r["peak_deviation_C"], 2),
                     "status": r["status"], "alert_episodes": len(ep), "log_vs_event_file_matched": cross["matched"],
                     "missing_seq": seq["missing"], "duplicate_seq": seq["duplicates"]})
    out = pd.DataFrame(rows)
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    out.to_csv(os.path.join(ROOT, "docs", "m4_summary.csv"), index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
