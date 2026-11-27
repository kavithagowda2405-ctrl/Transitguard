import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
from estimator import update, time_to_limit
from simulator import simulate

def test_moves_toward_air():
    assert 5 < update(5, 25, 5, 1800) < 25

def test_steady_state():
    assert update(5, 5, 5, 1800) == 5

def test_one_tau_is_63_percent():
    assert abs(update(0, 10, 1800, 1800) - 6.32) < 0.01

def test_ttl_upper():
    assert abs(time_to_limit(5, 25, 8, 1800) - 292.5) < 1

def test_ttl_lower():
    assert 600 < time_to_limit(5, -5, 2, 1800) < 700

def test_ttl_none_when_air_in_range():
    assert time_to_limit(5, 6, 8, 1800) is None

def test_door_spike_payload_stays_in_range():
    rows, _ = simulate("door", seed=1)
    assert max(r["t_air"] for r in rows) > 8
    assert max(r["t_pay"] for r in rows) < 8

def test_failure_crosses_upper_limit():
    rows, _ = simulate("failure", seed=1)
    assert max(r["t_pay"] for r in rows) > 8

def test_freeze_crosses_lower_limit():
    rows, _ = simulate("freeze", seed=1)
    assert min(r["t_pay"] for r in rows) < 2