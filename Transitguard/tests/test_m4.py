import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
import numpy as np
import pandas as pd
from log_tools import load_log, load_events, check_sequence
from events import door_events, door_test_summary, door_aware_alerts, crosscheck_door, alert_episodes
from risk import risk_status
from calibrate import calibrate, apply_calibration

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def _df(air, pay, door, est=None, ttl=None, dt=5):
    n = len(air)
    return pd.DataFrame({"seq": range(n), "epoch": 1764000000 + np.arange(n) * dt, "t_air": air, "t_pay": pay,
                         "door": door, "t_est": est if est is not None else pay, "ttl_s": ttl if ttl is not None else np.nan,
                         "time_s": np.arange(n) * dt})


def test_door_events_durations():
    d = np.zeros(30, int); d[5:8] = 1; d[20] = 1
    ev = door_events(_df(np.full(30, 4.0), np.full(30, 4.0), d))
    assert len(ev) == 2 and ev[0]["duration_s"] == 15.0 and ev[1]["duration_s"] == 5.0


def test_door_scenario_matches_event_file():
    df = load_log(os.path.join(DATA, "log_door_0.csv"))
    cross = crosscheck_door(df, load_events(os.path.join(DATA, "events_door_0.csv")))
    assert cross["log_events"] == 3 and cross["matched"] == 3


def test_door_summary_shows_air_spike_payload_steady():
    s = door_test_summary(load_log(os.path.join(DATA, "log_door_0.csv")))
    assert len(s) == 3 and (s["air_rise_C"] > 5).all() and (s["payload_change_C"].abs() < 1.0).all()


def test_no_false_alert_on_normal_and_door_runs():
    for name in ("normal", "door"):
        df = load_log(os.path.join(DATA, f"log_{name}_0.csv"))
        assert not door_aware_alerts(df).any(), name


def test_alert_on_failure_and_freeze_runs():
    for name in ("failure", "freeze"):
        df = load_log(os.path.join(DATA, f"log_{name}_0.csv"))
        assert door_aware_alerts(df).any(), name


def test_door_left_open_alerts():
    n = 100
    d = np.zeros(n, int); d[10:60] = 1          # 250 s open
    a = door_aware_alerts(_df(np.full(n, 4.0), np.full(n, 4.0), d))
    assert a.any()


def test_sequence_check_start_zero():
    r = check_sequence([0, 1, 2, 2, 4])
    assert r["missing"] == 1 and r["duplicates"] == 1 and r["missing_list"] == [3]


def test_risk_status_levels():
    n = 200
    assert risk_status(_df(np.full(n, 4.0), np.full(n, 4.0), np.zeros(n, int)))["status"] == "SAFE"
    p = np.full(n, 4.0); p[100:140] = 12.0
    assert risk_status(_df(np.full(n, 4.0), p, np.zeros(n, int)))["status"] in ("WARNING", "COMPROMISED")


def test_risk_counts_missing_values():
    p = np.full(50, 4.0); p[10] = np.nan
    r = risk_status(_df(np.full(50, 4.0), p, np.zeros(50, int)))
    assert r["missing_values"] == 1


def test_calibration_recovers_offset_and_gain():
    rng = np.random.default_rng(0)
    ref = np.repeat([0.0, 5.0, 25.0], 30)
    rows = pd.DataFrame({"probe": "air", "reference_c": ref, "reading_c": 1.01 * ref + 0.4 + rng.normal(0, 0.05, len(ref))})
    c = calibrate(rows)["air"]
    assert abs(c["slope_a"] - 1.01) < 0.01 and abs(c["offset_b"] - 0.4) < 0.1
    assert abs(apply_calibration(5 * 1.01 + 0.4, c) - 5.0) < 0.1


def test_loader_accepts_csvlogger_columns():
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "x.csv")
        open(p, "w").write("seq,timestamp,t0_air_c,t1_pay_c,t2_out_c,lid,status\n1,1000,4.0,4.5,28,0,OK\n2,1005,NaN,4.5,28,1,OK\n")
        df = load_log(p)
        assert list(df["t_air"].isna()) == [False, True] and df["door"].tolist() == [0, 1] and df["time_s"].tolist() == [0.0, 5.0]


def test_report_pdf_is_created():
    from report import make_report
    with tempfile.TemporaryDirectory() as tmp:
        pdf = os.path.join(tmp, "r.pdf")
        make_report(os.path.join(DATA, "log_ajar_0.csv"), pdf, os.path.join(DATA, "events_ajar_0.csv"))
        assert os.path.getsize(pdf) > 5000
