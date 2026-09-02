from ullm.metrics import aspectual_awareness_gap, teleological_bias_rate


def test_original_metrics():
    groups = ["A_x", "B_x", "C_x", "D_x"]
    gold = ["False", "True", "Unknown", "True"]
    pred = ["False", "True", "True", "True"]
    assert teleological_bias_rate(groups, pred) == 1.0
    assert aspectual_awareness_gap(groups, gold, pred) == 0.0
