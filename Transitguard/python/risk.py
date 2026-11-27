"""M4: risk status with demonstration limits. These are examples, not a product-release decision."""
import numpy as np
from log_tools import sample_interval

HIGH, LOW = 8.0, 2.0
DEMO_LIMITS = {"warn_door_s": 300, "warn_degmin": 1.0, "bad_degmin": 30.0}


def risk_status(df, column="t_pay", limits=None, high=HIGH, low=LOW):
    """SAFE / WARNING / COMPROMISED from degree-minutes outside the range and total lid-open time.
    column: use the payload probe (t_pay) or the estimate (t_est). Missing readings are skipped and counted."""
    lim = dict(DEMO_LIMITS)
    if limits:
        lim.update(limits)
    p = df[column].values.astype(float)
    missing = int(np.isnan(p).sum())
    p = np.where(np.isnan(p), np.nan, p)
    over = np.nan_to_num(np.clip(p - high, 0, None) + np.clip(low - p, 0, None), nan=0.0)
    dt = sample_interval(df)
    degmin = float(over.sum() * dt / 60.0)
    door = df["door"].values.astype(int)
    opens = int(((door[1:] == 1) & (door[:-1] == 0)).sum() + (1 if door[0] == 1 else 0))
    open_s = float(door.sum() * dt)
    if degmin >= lim["bad_degmin"]:
        status = "COMPROMISED"
    elif degmin >= lim["warn_degmin"] or open_s >= lim["warn_door_s"]:
        status = "WARNING"
    else:
        status = "SAFE"
    return {"status": status, "degree_minutes": degmin, "time_outside_s": float((over > 0).sum() * dt),
            "peak_deviation_C": float(over.max()), "door_opens": opens, "door_open_s": open_s,
            "missing_values": missing, "column": column}
