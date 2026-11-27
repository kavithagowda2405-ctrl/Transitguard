import csv, os, random
from estimator import update, time_to_limit

LOW, HIGH = 2.0, 8.0
AMBIENT, SETPOINT = 28.0, 4.0
DT = 5                       # seconds per reading
TAU_PAY = 1800.0             # placeholder, replace after step test
START_EPOCH = 1764000000
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# doors = (start_s, duration_s)
SCENARIOS = {
    "normal":  dict(doors=[]),
    "door":    dict(doors=[(1200, 15), (3000, 15), (5000, 60)]),
    "ajar":    dict(doors=[(1800, 300)]),
    "failure": dict(doors=[], fail_at=1800),
    "freeze":  dict(doors=[], freeze_at=1800),
}

def _ttl(t_est, t_air, tau):
    for limit in (HIGH, LOW):
        v = time_to_limit(t_est, t_air, limit, tau)
        if v is not None:
            return round(v, 1)
    return ""

def simulate(name, seed=0, duration=7200, tau_pay=TAU_PAY, tau_model=None):
    cfg = SCENARIOS[name]
    rng = random.Random(seed)
    tau_model = tau_model or tau_pay
    t_air, t_pay, t_est = SETPOINT, 5.0, 5.0
    rows, events = [], [dict(seq=0, epoch=START_EPOCH, event="BOOT", detail="")]
    was_open, open_since = 0, 0

    for i in range(duration // DT):
        t = i * DT
        door = int(any(s <= t < s + d for s, d in cfg["doors"]))
        target, tau_air = SETPOINT, 120.0
        if door:
            target, tau_air = AMBIENT, 60.0
        elif cfg.get("fail_at") is not None and t >= cfg["fail_at"]:
            target, tau_air = AMBIENT, 600.0
        elif cfg.get("freeze_at") is not None and t >= cfg["freeze_at"]:
            target, tau_air = -4.0, 300.0

        t_air = update(t_air, target, DT, tau_air)
        t_pay = update(t_pay, t_air, DT, tau_pay)
        air_m = t_air + rng.gauss(0, 0.1)      # measured values
        pay_m = t_pay + rng.gauss(0, 0.05)
        t_est = update(t_est, air_m, DT, tau_model)

        epoch = START_EPOCH + t
        if door and not was_open:
            open_since = t
            events.append(dict(seq=i, epoch=epoch, event="DOOR_OPEN", detail=""))
        if was_open and not door:
            events.append(dict(seq=i, epoch=epoch, event="DOOR_CLOSE",
                               detail=t - open_since))
        was_open = door

        rows.append(dict(seq=i, epoch=epoch, t_air=round(air_m, 3),
                         t_pay=round(pay_m, 3), door=door,
                         t_est=round(t_est, 3),
                         ttl_s=_ttl(t_est, air_m, tau_model), alert=0))
    return rows, events

def save(name, seed):
    os.makedirs(DATA_DIR, exist_ok=True)
    rows, events = simulate(name, seed)
    for fname, data in ((f"log_{name}_{seed}.csv", rows),
                        (f"events_{name}_{seed}.csv", events)):
        with open(os.path.join(DATA_DIR, fname), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            w.writeheader()
            w.writerows(data)

if __name__ == "__main__":
    for name in SCENARIOS:
        for seed in range(4):          # 5 scenarios x 4 seeds = 20 runs
            save(name, seed)
    print("Done: 20 runs saved in data/")