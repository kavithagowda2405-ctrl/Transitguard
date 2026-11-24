
import os
import sys

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "python")
)

from baselines import check_temperature
from alerts import generate_alert
from evaluate import evaluate_predictions
from simulator import simulate


# Temperature detection tests

def test_high_temperature_detection():
    assert check_temperature({"t_pay": 9.0}) == "HIGH"


def test_low_temperature_detection():
    assert check_temperature({"t_pay": 1.0}) == "LOW"


def test_normal_temperature_detection():
    assert check_temperature({"t_pay": 5.0}) == "NORMAL"


# Alert generation tests

def test_high_temperature_alert():
    alert = generate_alert("HIGH", 9.0)
    assert alert["level"] == "CRITICAL"


def test_low_temperature_alert():
    alert = generate_alert("LOW", 1.0)
    assert alert["level"] == "CRITICAL"


def test_normal_temperature_alert():
    alert = generate_alert("NORMAL", 5.0)
    assert alert["level"] == "NORMAL"


# Evaluation test

def test_evaluation_accuracy():
    result = evaluate_predictions(
        ["NORMAL", "HIGH", "LOW"],
        ["NORMAL", "HIGH", "NORMAL"]
    )

    assert result["accuracy"] == 66.67


# Simulator integration test

def test_simulator_failure_alert():
    rows, _ = simulate("failure", seed=1)

    statuses = [check_temperature(row) for row in rows]

    alerts = [
        generate_alert(status, row["t_pay"])
        for status, row in zip(statuses, rows)
    ]

    assert any(
        alert["level"] == "CRITICAL"
        for alert in alerts
    )
