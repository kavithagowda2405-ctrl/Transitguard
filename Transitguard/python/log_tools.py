"""M4: load logs and events, check sequence numbers.
Works with the simulator/device format (seq,epoch,t_air,t_pay,door,t_est,ttl_s,alert) and, through column
aliases, with the CSVLogger format (seq,timestamp,t0_air_c,t1_pay_c,t2_out_c,lid,status)."""
import numpy as np
import pandas as pd

ALIASES = {"timestamp": "epoch", "t0_air_c": "t_air", "t1_pay_c": "t_pay", "t2_out_c": "t_out", "lid": "door"}


def load_log(path):
    """Read a log CSV, rename aliased columns, add time_s (seconds since the first row).
    Missing values ('NaN' or empty) stay missing, never filled in.
    NOTE: for the CSVLogger format, confirm that lid = 1 means OPEN before trusting door results."""
    df = pd.read_csv(path, na_values=["NaN", "nan", ""])
    df = df.rename(columns={k: v for k, v in ALIASES.items() if k in df.columns and v not in df.columns})
    for need in ("epoch", "t_air", "t_pay", "door"):
        if need not in df.columns:
            raise ValueError(f"{path}: missing column '{need}' (found {list(df.columns)})")
    df["door"] = df["door"].fillna(0).astype(int)
    df["time_s"] = df["epoch"].astype(float) - float(df["epoch"].iloc[0])
    return df


def load_events(path):
    return pd.read_csv(path, na_values=["NaN", "nan", ""])


def sample_interval(df):
    return float(np.median(np.diff(df["time_s"].values))) if len(df) > 1 else 1.0


def check_sequence(seq):
    """Missing and duplicate sequence numbers (evidence for the offline-reliability experiment).
    Works for logs that start at 0 or 1."""
    s = np.asarray(seq).astype(int)
    if len(s) == 0:
        return {"records": 0, "missing": 0, "duplicates": 0, "first": None, "last": None, "missing_list": []}
    uniq = np.unique(s)
    expected = set(range(int(uniq[0]), int(uniq[-1]) + 1))
    missing = sorted(expected - set(uniq.tolist()))
    return {"records": int(len(s)), "missing": len(missing), "duplicates": int(len(s) - len(uniq)),
            "first": int(uniq[0]), "last": int(uniq[-1]), "missing_list": missing[:50]}
