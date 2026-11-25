
LOW_TEMP = 2.0
HIGH_TEMP = 8.0


def threshold_baseline(temperature):
    """
    Checks whether the temperature is within the safe range.
    """

    if temperature < LOW_TEMP:
        return "LOW"

    elif temperature > HIGH_TEMP:
        return "HIGH"

    else:
        return "NORMAL"


def check_temperature(row):
    """
    Checks the payload temperature from a simulator data row.
    """

    temperature = row["t_pay"]

    return threshold_baseline(temperature)
