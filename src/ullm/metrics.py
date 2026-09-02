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
            score += float(mask.mean()) * abs(float(corr[mask].mean()) - float(conf[mask].mean()))
    return score


def classwise_ece(gold: list[str], probs: list[dict[str, float]], n_bins: int = 15) -> float:
    """Average one-vs-rest ECE over True/False/Unknown."""
    if not gold:
        return float("nan")
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    values: list[float] = []
    for label in LABELS:
        conf = np.asarray([pr[label] for pr in probs], dtype=float)
        target = np.asarray([g == label for g in gold], dtype=float)
        score = 0.0
        for i in range(n_bins):
            left, right = edges[i], edges[i + 1]
            mask = (conf > left) & (conf <= right) if i else (conf >= left) & (conf <= right)
            if np.any(mask):
                score += float(mask.mean()) * abs(float(target[mask].mean()) - float(conf[mask].mean()))
        values.append(score)
    return float(np.mean(values))


def reliability_bins(
    gold: list[str], pred: list[str], probs: list[dict[str, float]], n_bins: int = 15
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


def group_accuracy(groups: list[str], gold: list[str], pred: list[str]) -> dict[str, float]:
    out: dict[str, float] = {}
    for letter in "ABCD":
        idx = [i for i, g in enumerate(groups) if g.startswith(letter + "_")]
        out[letter] = accuracy([gold[i] for i in idx], [pred[i] for i in idx])
    return out


def aspectual_awareness_gap(groups: list[str], gold: list[str], pred: list[str]) -> float:
    ga = group_accuracy(groups, gold, pred)
    return ga["D"] - teleological_bias_rate(groups, pred)


def semantic_uncertainty_recognition(groups: list[str], probs: list[dict[str, float]]) -> float:
    vals = [pr["Unknown"] for g, pr in zip(groups, probs) if g.startswith("C_")]
    return float(np.mean(vals)) if vals else float("nan")


def teleological_overconfidence_rate(
    groups: list[str], probs: list[dict[str, float]], threshold: float = 0.80
) -> float:
    vals = [pr["True"] >= threshold for g, pr in zip(groups, probs) if g.startswith("C_")]
    return float(np.mean(vals)) if vals else float("nan")


def ambiguity_discrimination_gap(groups: list[str], probs: list[dict[str, float]]) -> float:
    c = [pr["Unknown"] for g, pr in zip(groups, probs) if g.startswith("C_")]
    other = [pr["Unknown"] for g, pr in zip(groups, probs) if not g.startswith("C_")]
    return float(np.mean(c) - np.mean(other)) if c and other else float("nan")


def sampling_uncertainty(labels: list[str]) -> dict[str, float]:
    if not labels:
        return {"variation_ratio": float("nan"), "label_entropy": float("nan")}
    counts = Counter(labels)
    n = len(labels)
    ps = [counts[k] / n for k in LABELS if counts[k]]
    entropy = -sum(p * math.log(p) for p in ps) / math.log(len(LABELS))
    return {"variation_ratio": 1.0 - max(counts.values()) / n, "label_entropy": entropy}


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
    """Average precision for failure detection; higher score = more uncertain/error-prone."""
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


def risk_coverage(
    correct: list[bool], uncertainty: list[float]
) -> tuple[np.ndarray, np.ndarray, float]:
    """Selective risk curve, answering least-uncertain examples first."""
    if not correct:
        return np.array([]), np.array([]), float("nan")
    u = np.asarray(uncertainty, dtype=float)
    c = np.asarray(correct, dtype=float)
    valid = np.isfinite(u)
    u, c = u[valid], c[valid]
    order = np.argsort(u, kind="mergesort")
    c = c[order]
    risks, coverages = [], []
    for k in range(1, len(c) + 1):
        coverages.append(k / len(c))
        risks.append(1.0 - float(c[:k].mean()))
    cov, risk = np.asarray(coverages), np.asarray(risks)
    aurc = float(np.trapz(risk, cov)) if len(cov) > 1 else float(risk[0])
    return cov, risk, aurc


def excess_aurc(correct: list[bool], uncertainty: list[float]) -> float:
    """Empirical excess AURC above an oracle that answers all correct items first."""
    _, _, observed = risk_coverage(correct, uncertainty)
    oracle_uncertainty = [0.0 if ok else 1.0 for ok in correct]
    _, _, oracle = risk_coverage(correct, oracle_uncertainty)
    return observed - oracle


def jensen_shannon(p: dict[str, float], q: dict[str, float], eps: float = 1e-12) -> float:
    """Normalized Jensen-Shannon divergence in [0,1] for the three label distributions."""
    a = np.asarray([max(eps, p[k]) for k in LABELS], dtype=float)
    b = np.asarray([max(eps, q[k]) for k in LABELS], dtype=float)
    a = a / a.sum()
    b = b / b.sum()
    m = 0.5 * (a + b)
    kl_a = float(np.sum(a * np.log(a / m)))
    kl_b = float(np.sum(b * np.log(b / m)))
    return 0.5 * (kl_a + kl_b) / math.log(2.0)
