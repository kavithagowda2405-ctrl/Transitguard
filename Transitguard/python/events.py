"""M4: lid events, door-test summary, door-aware alert logic on log columns, alert episodes, event labels.
Uses only columns that are already in the log (t_air, t_pay, door, t_est, ttl_s), so it matches the device."""
import numpy as np
import pandas as pd
from log_tools import sample_interval

HIGH, LOW = 8.0, 2.0


def door_events(df):
    """Lid events from the door column: open time, close time, duration (seconds)."""
    t = df["time_s"].values.astype(float)
    d = df["door"].values.astype(int)
    dt = sample_interval(df)
    out, start = [], None
    for i, v in enumerate(d):
        if v and start is None:
            start = i
        if not v and start is not None:
            out.append((start, i - 1)); start = None
    if start is not None:
        out.append((start, len(d) - 1))
    return [{"open_idx": s, "close_idx": e, "open_time_s": float(t[s]), "close_time_s": float(t[e] + dt),
             "duration_s": float(t[e] - t[s] + dt)} for s, e in out]


def crosscheck_door(df, events_df, tol_s=None):
    """Compare lid events from the log with DOOR_OPEN/DOOR_CLOSE rows in the events file.
    Returns counts of events in each and how many have a matching open time."""
    dt = sample_interval(df)
    tol = tol_s if tol_s is not None else 2 * dt
    from_log = door_events(df)
    opens = events_df[events_df["event"] == "DOOR_OPEN"]["epoch"].astype(float).values - float(df["epoch"].iloc[0])
    matched = sum(1 for e in from_log if np.any(np.abs(opens - e["open_time_s"]) <= tol))
    return {"log_events": len(from_log), "event_file_opens": int(len(opens)), "matched": int(matched)}


def door_test_summary(df, recovery_tol=1.0, window_s=900):
    """One row per lid event: air before, air peak, air rise, payload change, air recovery time.
    Recovery time = seconds after closing until the air is within recovery_tol of its pre-open value (NaN if not within window_s)."""
    t = df["time_s"].values.astype(float)
    air = df["t_air"].values.astype(float)
    pay = df["t_pay"].values.astype(float)
    dt = sample_interval(df)
    rows = []
    for ev in door_events(df):
        s, e = ev["open_idx"], ev["close_idx"]
        pre = air[max(0, s - max(1, int(60 / dt))):s] if s > 0 else air[s:s + 1]
        base = float(np.nanmean(pre)) if len(pre) else float(air[s])
        end = min(len(t) - 1, e + int(window_s / dt))
        peak = float(np.nanmax(air[s:end + 1]))
        rec = np.nan
        for i in range(e + 1, end + 1):
            if air[i] <= base + recovery_tol:
                rec = float(t[i] - (t[e] + dt)); break
        rows.append({"opened_at_s": ev["open_time_s"], "open_s": ev["duration_s"], "air_before_C": base,
                     "air_peak_C": peak, "air_rise_C": peak - base,
                     "payload_change_C": float(pay[end] - pay[s]), "air_recovery_s": rec})
    return pd.DataFrame(rows)


def door_aware_alerts(df, horizon_s=600, debounce_n=3, hold_s=300, max_open_s=120, high=HIGH, low=LOW):
    """Alert decision from log columns. Same rules as the firmware:
    raw alert if the estimate is beyond a limit, OR the logged time-to-limit is within the horizon while the lid is
    closed (and was not opened in the last hold_s), OR the lid has been open longer than max_open_s.
    An alert needs debounce_n consecutive raw alerts."""
    est = df["t_est"].values.astype(float)
    ttl = pd.to_numeric(df["ttl_s"], errors="coerce").values if "ttl_s" in df.columns else np.full(len(df), np.nan)
    door = df["door"].values.astype(int)
    dt = sample_interval(df)
    raw = np.zeros(len(df), dtype=bool)
    open_s, since_close = 0.0, 1e9
    for i in range(len(df)):
        if door[i]:
            open_s += dt; since_close = 0.0
        else:
            open_s = 0.0; since_close += dt
        hold = bool(door[i]) or since_close < hold_s
        r = est[i] >= high or est[i] <= low
        if not hold and not np.isnan(ttl[i]) and ttl[i] <= horizon_s:
            r = True
        if door[i] and open_s > max_open_s:
            r = True
        raw[i] = r
    out, run = np.zeros(len(df), dtype=bool), 0
    for i, r in enumerate(raw):
        run = run + 1 if r else 0
        out[i] = run >= debounce_n
    return out


def alert_episodes(alert, time_s):
    out, start = [], None
    for i, a in enumerate(alert):
        if a and start is None:
            start = i
        if not a and start is not None:
            out.append({"start_s": float(time_s[start]), "end_s": float(time_s[i - 1])}); start = None
    if start is not None:
        out.append({"start_s": float(time_s[start]), "end_s": float(time_s[-1])})
    return pd.DataFrame(out, columns=["start_s", "end_s"])


def classify_samples(df, rate_window_s=300, door_hold_s=300):
    """Rule-based label per sample: DOOR, FREEZE_RISK, COOLING_FAILURE or NORMAL. Not validated on real runs."""
    est = df["t_est"].values.astype(float)
    air = df["t_air"].values.astype(float)
    door = df["door"].values.astype(int)
    dt = sample_interval(df)
    w = max(1, int(rate_window_s / dt))
    labels, since = [], 1e9
    for i in range(len(df)):
        since = 0.0 if door[i] else since + dt
        rate = (est[i] - est[max(0, i - w)]) / (w * dt) * 60.0     # degrees C per minute
        if est[i] <= LOW + 0.5 or (rate < -0.1 and est[i] < LOW + 1.5):
            labels.append("FREEZE_RISK")
        elif door[i] or since < door_hold_s:
            labels.append("DOOR")
        elif rate > 0.02 and air[i] > est[i] + 1.0:
            labels.append("COOLING_FAILURE")
        else:
            labels.append("NORMAL")
    return labels
