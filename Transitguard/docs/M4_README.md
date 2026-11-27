# M4: events, risk status, report, calibration and log tools

Owner: Member 4. Built for this repository's structure and data format. All files work on the simulator/device log
format already in `data/` (`log_*.csv`: seq, epoch, t_air, t_pay, door, t_est, ttl_s, alert; `events_*.csv`:
seq, epoch, event, detail). No other file in the repo is changed.

## Files added
| File | What it does |
|---|---|
| `python/log_tools.py` | Loads logs and events. Accepts the CSVLogger column names too (timestamp, t0_air_c, t1_pay_c, t2_out_c, lid). Missing values stay missing. Sequence check: missing and duplicate numbers |
| `python/events.py` | Lid events from the log, cross-check against the events file, door-test summary (air peak, payload change, air recovery time), door-aware alert rules on the logged estimate and time-to-limit, alert episodes, rule-based event labels |
| `python/risk.py` | Risk status: SAFE / WARNING / COMPROMISED from degree-minutes outside 2-8 C and total lid-open time (demonstration limits) |
| `python/calibrate.py` | Probe error table and linear correction against the reference thermometer |
| `python/report.py` | Two-page PDF report for one run |
| `python/summary_all.py` | One summary row per run in `data/`, written to `docs/m4_summary.csv` |
| `tests/test_m4.py` | 12 tests. Run with `python -m pytest` (the existing 19 tests still pass: 31 in total) |
| `docs/m4_summary.csv`, `docs/report_door_0.pdf` | Output on the simulated runs |
| `data/EXAMPLE_calibration_NOT_MEASURED.csv` | Made-up example of the calibration file format. Not a measurement |
| `docs/M4_REPO_REVIEW.md` | What I found when comparing with the rest of the repo |

## Run
    python -m pytest                                     # all tests
    python python/summary_all.py                         # table for all 20 runs
    python python/report.py data/log_door_0.csv docs/report_door_0.pdf data/events_door_0.csv
    python python/calibrate.py cal_data.csv calibration.json
    python python/report.py data/log_x.csv out.pdf data/events_x.csv calibration.json   # with calibration applied

## Alert rules (same as the firmware plan)
A raw alert happens if: the estimate is beyond 8 or 2 C; OR the logged time-to-limit is 600 s or less while the lid is
closed and was not opened in the last 300 s; OR the lid has been open longer than 120 s. An alert needs 3 raw alerts in
a row. Every lid event is logged, never ignored.

## Result on the simulated runs (SYNTHETIC: tests the code, not an experiment)
| Scenario | Lid openings | Status | Alert episodes |
|---|---|---|---|
| normal | 0 | SAFE | 0 |
| door (3 short openings) | 3 | SAFE | 0 (the air spikes, the payload stays in range) |
| ajar (lid open 300 s) | 1 | WARNING | 2 |
| failure (cooling lost) | 0 | COMPROMISED | 1 |
| freeze | 0 | COMPROMISED | 1 |
The lid events in each log match its events file in every run.

## Definitions
- Air recovery time: seconds after closing until the air is within 1 C of its value before opening (15 minute window).
- Degree-minutes: how far the payload probe is outside 2-8 C, summed over time, in degree-minutes.
- Risk limits (`DEMO_LIMITS` in `risk.py`) are demonstration limits, not a product-release decision.

## Honest notes
- Everything is tested on simulated data only. The payload is a test payload, and nothing here shows real vaccine potency.
- The event labels are simple rules and have not been checked against real labelled runs.
- The alert rules use the `t_est` and `ttl_s` columns written by the logger or simulator. If the model time constant
  used there is wrong, the alerts are wrong, so the real tau must be fitted first.
