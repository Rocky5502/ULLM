import math

from ullm.metrics import (
    ambiguity_discrimination_gap,
    average_precision,
    binary_auroc,
    excess_aurc,
    jensen_shannon,
    normalized_entropy,
    risk_coverage,
    semantic_uncertainty_recognition,
    teleological_overconfidence_rate,
)


def test_group_c_semantic_metrics():
    groups = ["A_x", "B_x", "C_x", "D_x"]
    probs = [
        {"True": 0.05, "False": 0.90, "Unknown": 0.05},
        {"True": 0.90, "False": 0.05, "Unknown": 0.05},
        {"True": 0.05, "False": 0.05, "Unknown": 0.90},
        {"True": 0.90, "False": 0.05, "Unknown": 0.05},
    ]
    assert semantic_uncertainty_recognition(groups, probs) == 0.90
    assert teleological_overconfidence_rate(groups, probs, 0.80) == 0.0
    assert math.isclose(ambiguity_discrimination_gap(groups, probs), 0.85)


def test_entropy_distinguishes_sharp_and_uniform():
    sharp = normalized_entropy({"True": 0.0, "False": 0.0, "Unknown": 1.0})
    uniform = normalized_entropy({"True": 1/3, "False": 1/3, "Unknown": 1/3})
    assert sharp < 1e-8
    assert math.isclose(uniform, 1.0, rel_tol=1e-8)


def test_failure_ranking_perfect_order():
    target = [False, False, True, True]
    score = [0.1, 0.2, 0.8, 0.9]
    assert binary_auroc(target, score) == 1.0
    assert average_precision(target, score) == 1.0


def test_risk_coverage_good_uncertainty_beats_oracle_gap_zero():
    correct = [True, True, False, False]
    uncertainty = [0.1, 0.2, 0.8, 0.9]
    coverage, risk, aurc = risk_coverage(correct, uncertainty)
    assert len(coverage) == 4
    assert risk[0] == 0.0
    assert aurc >= 0.0
    assert math.isclose(excess_aurc(correct, uncertainty), 0.0, abs_tol=1e-12)


def test_jsd_identity_and_symmetry():
    p = {"True": 0.1, "False": 0.2, "Unknown": 0.7}
    q = {"True": 0.7, "False": 0.2, "Unknown": 0.1}
    assert math.isclose(jensen_shannon(p, p), 0.0, abs_tol=1e-12)
    assert math.isclose(jensen_shannon(p, q), jensen_shannon(q, p), rel_tol=1e-12)
    assert 0.0 < jensen_shannon(p, q) <= 1.0
