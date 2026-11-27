"""M4: two-page PDF journey report from a log CSV (and optionally its events CSV).
Usage: python python/report.py data/log_door_0.csv docs/report_door_0.pdf [data/events_door_0.csv] [calibration.json]"""
import json
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
sys.path.insert(0, os.path.dirname(__file__))
from log_tools import load_log, load_events, sample_interval, check_sequence
from events import (door_test_summary, door_aware_alerts, alert_episodes, classify_samples, crosscheck_door, HIGH, LOW)
from risk import risk_status, DEMO_LIMITS
from calibrate import apply_calibration


def _table(ax, df, title):
    ax.axis("off")
    ax.set_title(title, fontsize=10, loc="left", weight="bold")
    if df is None or len(df) == 0:
        ax.text(0.0, 0.8, "None recorded", fontsize=9); return
    cells = [[("n/a" if pd.isna(v) else f"{v:.1f}") for v in row] for row in df.itertuples(index=False)]
    tb = ax.table(cellText=cells, colLabels=list(df.columns), loc="upper left", cellLoc="center")
    tb.auto_set_font_size(False); tb.set_fontsize(7); tb.scale(1, 1.25)


def make_report(log_path, pdf_path, events_path=None, cal_path=None):
    df = load_log(log_path)
    if cal_path:
        cal = json.load(open(cal_path))
        if "air" in cal: df["t_air"] = apply_calibration(df["t_air"], cal["air"])
        if "payload" in cal: df["t_pay"] = apply_calibration(df["t_pay"], cal["payload"])
    dt = sample_interval(df)
    t = df["time_s"].values / 60.0
    risk = risk_status(df)
    doors = door_test_summary(df)
    alert = door_aware_alerts(df)
    episodes = alert_episodes(alert, df["time_s"].values)
    labels = classify_samples(df)
    seq = check_sequence(df["seq"]) if "seq" in df.columns else None
    cross = crosscheck_door(df, load_events(events_path)) if events_path else None
    rmse = float(np.sqrt(np.nanmean((df["t_est"].values - df["t_pay"].values) ** 2)))
    with PdfPages(pdf_path) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.08, 0.95, "TransitGuard journey report", fontsize=18, weight="bold")
        fig.text(0.08, 0.925, f"Source: {os.path.basename(log_path)}", fontsize=9)
        lines = [f"Duration: {t[-1]:.0f} min    Samples: {len(df)}    Missing payload-probe values: {risk['missing_values']}",
                 f"Status: {risk['status']}  (demonstration limits: warn at {DEMO_LIMITS['warn_degmin']} degree-min or {DEMO_LIMITS['warn_door_s']} s lid open; compromised at {DEMO_LIMITS['bad_degmin']} degree-min)",
                 f"Time outside {LOW:.0f}-{HIGH:.0f} C (payload probe): {risk['time_outside_s']/60:.1f} min    Peak deviation: {risk['peak_deviation_C']:.2f} C    Degree-minutes: {risk['degree_minutes']:.1f}",
                 f"Lid openings: {risk['door_opens']}    Total open time: {risk['door_open_s']:.0f} s",
                 f"Payload estimate vs probe: RMSE {rmse:.2f} C",
                 f"Sequence check: {seq['missing']} missing, {seq['duplicates']} duplicate of {seq['records']} records" if seq else "",
                 f"Lid events in log vs event file: {cross['log_events']} vs {cross['event_file_opens']} (matched {cross['matched']})" if cross else ""]
        for i, l in enumerate([x for x in lines if x]):
            fig.text(0.08, 0.89 - i * 0.022, l, fontsize=8.5)
        ax = fig.add_axes([0.08, 0.44, 0.86, 0.25])
        ax.plot(t, df["t_air"], label="Air probe", lw=0.8)
        ax.plot(t, df["t_pay"], label="Payload probe", lw=1.2)
        ax.plot(t, df["t_est"], "--", label="Payload estimate", lw=1.2)
        ax.axhline(HIGH, color="k", ls=":", lw=0.8); ax.axhline(LOW, color="k", ls=":", lw=0.8)
        lo, hi = ax.get_ylim()
        ax.fill_between(t, lo, hi, where=df["door"].values.astype(bool), color="grey", alpha=0.3, label="Lid open")
        ax.set_ylim(lo, hi); ax.set_xlabel("Time (min)"); ax.set_ylabel("Temperature (C)"); ax.legend(fontsize=7)
        ax2 = fig.add_axes([0.08, 0.08, 0.86, 0.26])
        counts = pd.Series(labels).value_counts()
        ax2.bar(counts.index, counts.values * dt / 60); ax2.set_ylabel("Minutes")
        ax2.set_title("Time by event label (rule-based)", fontsize=9)
        pdf.savefig(fig); plt.close(fig)
        fig2 = plt.figure(figsize=(8.27, 11.69))
        fig2.text(0.08, 0.95, "Events", fontsize=14, weight="bold")
        _table(fig2.add_axes([0.06, 0.55, 0.9, 0.35]), doors, "Lid openings (payload change measured 15 min after closing)")
        _table(fig2.add_axes([0.06, 0.22, 0.9, 0.25]), episodes, "Alert episodes (door-aware rules on the logged estimate and time-to-limit)")
        fig2.text(0.06, 0.06, "Limits shown are demonstration limits, not a product-release decision. The payload is a test payload;\nnothing here shows real vaccine potency or safety.", fontsize=8)
        pdf.savefig(fig2); plt.close(fig2)
    return {"risk": risk, "door_events": len(doors), "alert_episodes": len(episodes)}


if __name__ == "__main__":
    print(make_report(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None,
                      sys.argv[4] if len(sys.argv) > 4 else None))
