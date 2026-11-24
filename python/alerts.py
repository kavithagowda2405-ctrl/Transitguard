
def generate_alert(status, temperature):
    """
    Generates an alert based on temperature status.
    """

    if status == "LOW":
        return {
            "level": "CRITICAL",
            "message": f"Temperature too low: {temperature} °C"
        }

    elif status == "HIGH":
        return {
            "level": "CRITICAL",
            "message": f"Temperature too high: {temperature} °C"
        }

    else:
        return {
            "level": "NORMAL",
            "message": "Temperature is within safe limits"
        }
