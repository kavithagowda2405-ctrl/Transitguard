import csv, os
import numpy as np
from simulator import simulate, SCENARIOS

TAU_TRUE = 1800.0
TAU_MODELS = [900, 1350, 1800, 2250, 2700]   # -50% to +50%
DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(DOCS, exist_ok=True)

rows_out = []
for tm in TAU_MODELS:
    errs = []
    for name in SCENARIOS:
        for seed in range(4):
            rows, _ = simulate(name, seed, tau_pay=TAU_TRUE, tau_model=tm)
            errs += [r["t_est"] - r["t_pay"] for r in rows]
    e = np.array(errs)
    rows_out.append(dict(tau_model=tm,
                         mean_abs_err=round(float(np.abs(e).mean()), 3),
                         rmse=round(float(np.sqrt((e**2).mean())), 3),
                         max_abs_err=round(float(np.abs(e).max()), 3)))
    print(rows_out[-1])

with open(os.path.join(DOCS, "sensitivity.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows_out[0].keys())
    w.writeheader()
    w.writerows(rows_out)