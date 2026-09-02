from __future__ import annotations

import math
from collections import Counter
from typing import Iterable

import numpy as np

from .schemas import LABELS


def accuracy(gold: Iterable[str], pred: Iterable[str]) -> float:
    g, p = list(gold), list(pred)
    return float(np.mean([a == b for a, b in zip(g, p)])) if g else float("nan")


def multiclass_brier(gold: list[str], probs: list[dict[str, float]]) -> float:
    return float(np.mean([sum((pr[k] - float(k == y)) ** 2 for k in LABELS) for y, pr in zip(gold, probs)]))


def nll(gold: list[str], probs: list[dict[str, float]], eps: float = 1e-12) -> float:
    return float(np.mean([-math.log(max(eps, pr[y])) for y, pr in zip(gold, probs)]))


def normalized_entropy(prob: dict[str, float]) -> float:
    h = -sum(p * math.log(max(p, 1e-12)) for p in prob.values())
    return h / math.log(len(LABELS))


def ece(gold: list[str], pred: list[str], probs: list[dict[str, float]], n_bins: int = 10) -> float:
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


def teleological_bias_rate(groups: list[str], pred: list[str]) -> float:
    vals = [p == "True" for g, p in zip(groups, pred) if g.startswith("C_")]
    return float(np.mean(vals)) if vals else float("nan")


def group_accuracy(groups: list[str], gold: list[str], pred: list[str]) -> dict[str, float]:
    out = {}
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


def teleological_overconfidence_rate(groups: list[str], probs: list[dict[str, float]], threshold: float = 0.80) -> float:
    vals = [pr["True"] >= threshold for g, pr in zip(groups, probs) if g.startswith("C_")]
    return float(np.mean(vals)) if vals else float("nan")


def ambiguity_discrimination_gap(groups: list[str], probs: list[dict[str, float]]) -> float:
    c = [pr["Unknown"] for g, pr in zip(groups, probs) if g.startswith("C_")]
    other = [pr["Unknown"] for g, pr in zip(groups, probs) if not g.startswith("C_")]
    return float(np.mean(c) - np.mean(other))


def sampling_uncertainty(labels: list[str]) -> dict[str, float]:
    if not labels:
        return {"variation_ratio": float("nan"), "label_entropy": float("nan")}
    counts = Counter(labels)
    n = len(labels)
    ps = [counts[k] / n for k in LABELS if counts[k]]
    entropy = -sum(p * math.log(p) for p in ps) / math.log(len(LABELS))
    return {"variation_ratio": 1.0 - max(counts.values()) / n, "label_entropy": entropy}


def risk_coverage(correct: list[bool], uncertainty: list[float]) -> tuple[np.ndarray, np.ndarray, float]:
    order = np.argsort(np.asarray(uncertainty))
    c = np.asarray(correct, dtype=float)[order]
    risks, coverages = [], []
    for k in range(1, len(c) + 1):
        coverages.append(k / len(c))
        risks.append(1.0 - float(c[:k].mean()))
    cov, risk = np.asarray(coverages), np.asarray(risks)
    aurc = float(np.trapz(risk, cov)) if len(cov) > 1 else float(risk[0])
    return cov, risk, aurc
