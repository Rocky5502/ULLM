from __future__ import annotations

import math
from collections import Counter
from typing import Iterable

import numpy as np
from scipy.stats import rankdata

from .schemas import LABELS


def accuracy(gold: Iterable[str], pred: Iterable[str]) -> float:
    g, p = list(gold), list(pred)
    return float(np.mean([a == b for a, b in zip(g, p)])) if g else float("nan")


def multiclass_brier(gold: list[str], probs: list[dict[str, float]]) -> float:
    if not gold:
        return float("nan")
    return float(
        np.mean(
            [sum((pr[k] - float(k == y)) ** 2 for k in LABELS) for y, pr in zip(gold, probs)]
        )
    )


def nll(gold: list[str], probs: list[dict[str, float]], eps: float = 1e-12) -> float:
    if not gold:
        return float("nan")
    return float(np.mean([-math.log(max(eps, pr[y])) for y, pr in zip(gold, probs)]))


def normalized_entropy(prob: dict[str, float]) -> float:
    h = -sum(p * math.log(max(p, 1e-12)) for p in prob.values())
    return h / math.log(len(LABELS))


def prediction_confidence(prob: dict[str, float]) -> float:
    return float(max(prob.values()))


def verbal_uncertainty(prob: dict[str, float]) -> float:
    return 1.0 - prediction_confidence(prob)


# Backward-compatible name used by early analysis scripts.
def confidence_uncertainty(prob: dict[str, float]) -> float:
    return verbal_uncertainty(prob)


def ece(
    gold: list[str],
    pred: list[str],
    probs: list[dict[str, float]],
    n_bins: int = 15,
) -> float:
    """Top-label expected calibration error with equal-width bins."""
    if not gold:
        return float("nan")
    conf = np.array([max(pr.values()) for pr in probs], dtype=float)
    corr = np.array([a == b for a, b in zip(gold, pred)], dtype=float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    score = 0.0
    for i in range(n_bins):
        left, right = edges[i], edges[i + 1]
        mask = (conf > left) & (conf <= right) if i else (conf >= left) & (conf <= right)
        if np.any(mask):
            score += float(mask.mean()) * abs(
                float(corr[mask].mean()) - float(conf[mask].mean())
            )
    return score


def classwise_ece(
    gold: list[str], probs: list[dict[str, float]], n_bins: int = 15
) -> dict[str, float]:
    """One-vs-rest ECE for each label; Unknown is scientifically central here."""
    if not gold:
        return {k: float("nan") for k in LABELS}
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    values: dict[str, float] = {}
    for label in LABELS:
        conf = np.asarray([pr[label] for pr in probs], dtype=float)
        target = np.asarray([g == label for g in gold], dtype=float)
        score = 0.0
        for i in range(n_bins):
            left, right = edges[i], edges[i + 1]
            mask = (conf > left) & (conf <= right) if i else (conf >= left) & (conf <= right)
            if np.any(mask):
                score += float(mask.mean()) * abs(
                    float(target[mask].mean()) - float(conf[mask].mean())
                )
        values[label] = score
    return values


def mean_classwise_ece(
    gold: list[str], probs: list[dict[str, float]], n_bins: int = 15
) -> float:
    vals = classwise_ece(gold, probs, n_bins=n_bins)
    return float(np.mean(list(vals.values())))


def reliability_bins(
    gold: list[str],
    pred: list[str],
    probs: list[dict[str, float]],
    n_bins: int = 15,
) -> list[dict[str, float]]:
    """Data for reliability diagrams; empty bins are omitted."""
    conf = np.asarray([max(pr.values()) for pr in probs], dtype=float)
    corr = np.asarray([a == b for a, b in zip(gold, pred)], dtype=float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    rows: list[dict[str, float]] = []
    for i in range(n_bins):
        left, right = edges[i], edges[i + 1]
        mask = (conf > left) & (conf <= right) if i else (conf >= left) & (conf <= right)
        if np.any(mask):
            rows.append(
                {
                    "left": float(left),
                    "right": float(right),
                    "n": int(mask.sum()),
                    "confidence": float(conf[mask].mean()),
                    "accuracy": float(corr[mask].mean()),
                }
            )
    return rows


def teleological_bias_rate(groups: list[str], pred: list[str]) -> float:
    vals = [p == "True" for g, p in zip(groups, pred) if g.startswith("C_")]
    return float(np.mean(vals)) if vals else float("nan")


def group_accuracy(
    groups: list[str], gold: list[str], pred: list[str]
) -> dict[str, float]:
    out: dict[str, float] = {}
    for letter in "ABCD":
        idx = [i for i, g in enumerate(groups) if g.startswith(letter + "_")]
        out[letter] = accuracy([gold[i] for i in idx], [pred[i] for i in idx])
    return out


def aspectual_awareness_gap(
    groups: list[str], gold: list[str], pred: list[str]
) -> float:
    ga = group_accuracy(groups, gold, pred)
    return ga["D"] - teleological_bias_rate(groups, pred)


def semantic_uncertainty_recognition(
    groups: list[str], probs: list[dict[str, float]]
) -> float:
    vals = [pr["Unknown"] for g, pr in zip(groups, probs) if g.startswith("C_")]
    return float(np.mean(vals)) if vals else float("nan")


def teleological_overconfidence_rate(
    groups: list[str],
    probs: list[dict[str, float]],
    threshold: float = 0.80,
) -> float:
    vals = [
        pr["True"] >= threshold
        for g, pr in zip(groups, probs)
        if g.startswith("C_")
    ]
    return float(np.mean(vals)) if vals else float("nan")


def ambiguity_discrimination_gap(
    groups: list[str], probs: list[dict[str, float]]
) -> float:
    c = [pr["Unknown"] for g, pr in zip(groups, probs) if g.startswith("C_")]
    other = [
        pr["Unknown"] for g, pr in zip(groups, probs) if not g.startswith("C_")
    ]
    return float(np.mean(c) - np.mean(other)) if c and other else float("nan")


def sampling_uncertainty(labels: list[str]) -> dict[str, float]:
    if not labels:
        return {"variation_ratio": float("nan"), "label_entropy": float("nan")}
    counts = Counter(labels)
    n = len(labels)
    ps = [counts[k] / n for k in LABELS if counts[k]]
    entropy = -sum(p * math.log(p) for p in ps) / math.log(len(LABELS))
    return {"variation_ratio": 1.0 - max(counts.values()) / n, "label_entropy": entropy}


def paired_condition_consistency(records: list[dict]) -> dict[str, float]:
    """Exact paired correctness across A/C and B/D for matching numeric IDs.

    This is intentionally strict: a pair counts only when BOTH member predictions are
    correct. More granular probability-shift analysis lives in analyze_pairwise.py.
    """
    by_id = {r["example"]["id"]: r for r in records if r.get("prediction")}
    out: dict[str, float] = {}
    for name, left, right in (("AC", "A", "C"), ("BD", "B", "D")):
        ok: list[bool] = []
        for i in range(1, 101):
            a = by_id.get(f"{left}_{i:03d}")
            b = by_id.get(f"{right}_{i:03d}")
            if not a or not b:
                continue
            ok.append(
                a["prediction"]["label"] == a["example"]["label"]
                and b["prediction"]["label"] == b["example"]["label"]
            )
        out[name] = float(np.mean(ok)) if ok else float("nan")
    return out


def binary_auroc(target: list[bool], score: list[float]) -> float:
    """AUROC via rank statistic; score must increase with positive-class likelihood."""
    y = np.asarray(target, dtype=bool)
    s = np.asarray(score, dtype=float)
    valid = np.isfinite(s)
    y, s = y[valid], s[valid]
    n_pos = int(y.sum())
    n_neg = int((~y).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = rankdata(s, method="average")
    rank_sum_pos = float(ranks[y].sum())
    u = rank_sum_pos - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * n_neg)


def average_precision(target: list[bool], score: list[float]) -> float:
    """Average precision for failure detection; higher score = more error-prone."""
    y = np.asarray(target, dtype=bool)
    s = np.asarray(score, dtype=float)
    valid = np.isfinite(s)
    y, s = y[valid], s[valid]
    if y.sum() == 0:
        return float("nan")
    order = np.argsort(-s, kind="mergesort")
    y = y[order].astype(float)
    precision = np.cumsum(y) / np.arange(1, len(y) + 1)
    return float((precision * y).sum() / y.sum())


def _validated_selective_arrays(
    correct: list[bool], uncertainty: list[float]
) -> tuple[np.ndarray, np.ndarray]:
    if len(correct) != len(uncertainty):
        raise ValueError("correct and uncertainty must have the same length")
    c = np.asarray(correct, dtype=bool)
    u = np.asarray(uncertainty, dtype=float)
    valid = np.isfinite(u)
    return c[valid], u[valid]


def risk_coverage(
    correct: list[bool], uncertainty: list[float]
) -> tuple[np.ndarray, np.ndarray, float]:
    """Empirical selective-risk curve with order-invariant handling of tied scores.

    Lower uncertainty is answered first. Many black-box signals (especially K=5
    variation ratio) are highly discrete, so arbitrary ordering inside a tie can change
    AURC. For each tied uncertainty block we use the expected cumulative error under a
    uniformly random order within the tie. The returned curve still has one point per
    retained item, but is invariant to input order. AURC is the discrete mean selective
    risk over coverages 1/n,...,1, a common empirical definition for selective models.
    """
    if not correct:
        return np.array([]), np.array([]), float("nan")
    c, u = _validated_selective_arrays(correct, uncertainty)
    if len(c) == 0:
        return np.array([]), np.array([]), float("nan")

    order = np.argsort(u, kind="mergesort")
    c, u = c[order], u[order]
    n = len(c)
    coverages = np.arange(1, n + 1, dtype=float) / n
    risks = np.empty(n, dtype=float)

    errors_before = 0.0
    answered_before = 0
    start = 0
    while start < n:
        end = start + 1
        while end < n and u[end] == u[start]:
            end += 1
        block = c[start:end]
        block_n = len(block)
        block_errors = float((~block).sum())
        for j in range(1, block_n + 1):
            expected_errors = errors_before + j * (block_errors / block_n)
            risks[answered_before + j - 1] = expected_errors / (answered_before + j)
        errors_before += block_errors
        answered_before += block_n
        start = end

    aurc = float(np.mean(risks))
    return coverages, risks, aurc


def threshold_risk_coverage(
    correct: list[bool], uncertainty: list[float]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Risk/coverage points attainable by thresholding a possibly discrete score.

    Entire tied score blocks are accepted together. The third return value contains the
    uncertainty threshold associated with each point.
    """
    if not correct:
        return np.array([]), np.array([]), np.array([])
    c, u = _validated_selective_arrays(correct, uncertainty)
    if len(c) == 0:
        return np.array([]), np.array([]), np.array([])
    order = np.argsort(u, kind="mergesort")
    c, u = c[order], u[order]
    thresholds = np.unique(u)
    coverages: list[float] = []
    risks: list[float] = []
    for threshold in thresholds:
        keep = u <= threshold
        coverages.append(float(keep.mean()))
        risks.append(float((~c[keep]).mean()))
    return np.asarray(coverages), np.asarray(risks), thresholds


def select_indices_at_coverage(
    uncertainty: list[float], target: float
) -> tuple[list[int], float, float]:
    """Select a threshold-realizable set at or above target coverage.

    If the target cuts through a tied uncertainty block, the whole block is included so
    the selection is reproducible and does not exploit arbitrary row order. Returns
    original indices, achieved coverage, and the boundary uncertainty threshold.
    """
    if not 0.0 < target <= 1.0:
        raise ValueError("target coverage must be in (0, 1]")
    u = np.asarray(uncertainty, dtype=float)
    valid_idx = np.flatnonzero(np.isfinite(u))
    if len(valid_idx) == 0:
        return [], float("nan"), float("nan")
    valid_scores = u[valid_idx]
    order = np.argsort(valid_scores, kind="mergesort")
    ranked_scores = valid_scores[order]
    k = max(1, int(math.ceil(target * len(ranked_scores))))
    boundary = float(ranked_scores[k - 1])
    chosen_mask = valid_scores <= boundary
    chosen = valid_idx[chosen_mask].tolist()
    return chosen, len(chosen) / len(valid_idx), boundary


def excess_aurc(correct: list[bool], uncertainty: list[float]) -> float:
    """Empirical excess AURC above an oracle that answers correct items first."""
    _, _, observed = risk_coverage(correct, uncertainty)
    oracle_uncertainty = [0.0 if ok else 1.0 for ok in correct]
    _, _, oracle = risk_coverage(correct, oracle_uncertainty)
    return observed - oracle


def jensen_shannon(
    p: dict[str, float], q: dict[str, float], eps: float = 1e-12
) -> float:
    """Normalized Jensen-Shannon divergence in [0,1] for the three labels."""
    a = np.asarray([max(eps, p[k]) for k in LABELS], dtype=float)
    b = np.asarray([max(eps, q[k]) for k in LABELS], dtype=float)
    a = a / a.sum()
    b = b / b.sum()
    m = 0.5 * (a + b)
    kl_a = float(np.sum(a * np.log(a / m)))
    kl_b = float(np.sum(b * np.log(b / m)))
    return 0.5 * (kl_a + kl_b) / math.log(2.0)
