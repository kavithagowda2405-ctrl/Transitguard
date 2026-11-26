import csv, os
from estimator import update, time_to_limit

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "test_vector.csv")
air = [4.0]*60 + [28.0]*180 + [4.0]*120      # no noise, fixed input
t_est = 5.0
with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["i", "t_air", "t_est", "ttl_s"])
    for i, a in enumerate(air):
        t_est = update(t_est, a, 5, 1800.0)
        ttl = time_to_limit(t_est, a, 8.0, 1800.0)
        w.writerow([i, a, round(t_est, 4), "" if ttl is None else round(ttl, 1)])
print("saved", OUT)