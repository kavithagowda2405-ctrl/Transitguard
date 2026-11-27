"""Probe calibration against the reference thermometer.
Input CSV: probe,point,reference_c,reading_c (about 30 readings per probe and point).
Usage: python python/calibrate.py cal_data.csv calibration.json"""
import json
import sys
import numpy as np
import pandas as pd


def calibrate(df):
    out = {}
    for probe, g in df.groupby("probe"):
        ref, rd = g["reference_c"].values.astype(float), g["reading_c"].values.astype(float)
        err = rd - ref
        a, b = np.polyfit(ref, rd, 1)                    # reading = a * reference + b
        out[str(probe)] = {"n": int(len(g)), "mean_error_c": float(err.mean()),
                           "sd_error_c": float(err.std(ddof=1)) if len(g) > 1 else 0.0,
                           "max_abs_error_c": float(np.abs(err).max()), "slope_a": float(a), "offset_b": float(b),
                           "mean_abs_error_after_c": float(np.abs((rd - b) / a - ref).mean())}
    return out


def apply_calibration(reading, cal):
    return (reading - cal["offset_b"]) / cal["slope_a"]


if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else "calibration.json"
    res = calibrate(pd.read_csv(src))
    json.dump(res, open(dst, "w"), indent=2)
    print(pd.DataFrame(res).T[["n", "mean_error_c", "sd_error_c", "max_abs_error_c", "mean_abs_error_after_c"]].to_string(float_format=lambda v: f"{v:.3f}"))
    print("wrote", dst)
