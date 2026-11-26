# TransitGuard

Affordable ESP32-based embedded system for monitoring temperature-sensitive
products in transport. Mini Project (BEC586), Phase-I, Dept. of ECE, GSSSIETW.

## What it does
- Records air and payload temperature and logs every lid opening
- Estimates payload temperature from the air temperature (first-order lag)
  and predicts the time to the 2-8 °C limit
- Door-aware alerts compared with threshold-only alerts
- Offline-first numbered logging with hashes, and store-and-forward sync

## Status
Software and simulation only. The hardware is not built yet.
All results here come from synthetic data. They test the code and are not
experimental results. τ = 1800 s is a placeholder until a real step test.

## Folder structure
| Folder | Contents |
|---|---|
| `python/` | estimator, simulator, alerts, baselines, evaluation, logger, sync receiver, report |
| `tests/` | pytest tests |
| `firmware/` | ESP32 code (Wokwi simulation) |
| `data/` | simulated `log_*.csv` and `events_*.csv` |
| `docs/` | plots, slides, notes |

## Setup (Windows PowerShell)
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```
python python\simulator.py     # generate simulated data in data/
python python\plot.py          # save plots in docs/
pytest                         # run tests
```

## Data format
`log.csv`: seq, epoch, t_air, t_pay, door (1 = open), t_est, ttl_s, alert
`events.csv`: seq, epoch, event, detail

## Team
| Member | Role |
|---|---|
| Kavitha K C | Simulation core (estimator, simulator) |
| Rashmitha K N | Alerts, baselines, evaluation |
| Likhitha R | Logging, integrity, sync |
| Likhitha N | ESP32 firmware (Wokwi), reports |

## Limitations
Dummy payload only, not a certified device, no claims about vaccine potency
or safety. Results apply to our box and test conditions.