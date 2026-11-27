
def evaluate_predictions(actual, predicted):
    """
    Evaluates temperature detection results.
    """

    if len(actual) != len(predicted):
        raise ValueError("Actual and predicted lists must have equal length")

    total = len(actual)

    if total == 0:
        return {
            "accuracy": 0.0,
            "correct": 0,
            "total": 0
        }

    correct = sum(
        1 for a, p in zip(actual, predicted) if a == p
    )

    accuracy = (correct / total) * 100

    return {
        "accuracy": round(accuracy, 2),
        "correct": correct,
        "total": total
    }
