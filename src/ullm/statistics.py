from __future__ import annotations

from collections import defaultdict
from typing import Callable, Iterable, Sequence

import numpy as np


def cluster_bootstrap(
    values: Sequence[float],
    clusters: Sequence[str],
    statistic: Callable[[np.ndarray], float] = lambda x: float(np.mean(x)),
    *,
    n_boot: int = 10000,
    confidence: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Cluster bootstrap resampling whole verb clusters; returns point, low, high."""
    if len(values) != len(clusters) or not values:
        return float("nan"), float("nan"), float("nan")
    groups: dict[str, list[float]] = defaultdict(list)
    for v, c in zip(values, clusters):
        groups[str(c)].append(float(v))
    keys = sorted(groups)
    point = statistic(np.asarray(values, dtype=float))
    rng = np.random.default_rng(seed)
    boot = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        sampled = rng.choice(keys, size=len(keys), replace=True)
        sample = np.asarray([v for key in sampled for v in groups[key]], dtype=float)
        boot[b] = statistic(sample)
    alpha = 1.0 - confidence
    lo, hi = np.quantile(boot, [alpha / 2.0, 1.0 - alpha / 2.0])
    return float(point), float(lo), float(hi)


def holm_adjust(p_values: Iterable[float]) -> list[float]:
    p = np.asarray(list(p_values), dtype=float)
    if len(p) == 0:
        return []
    order = np.argsort(p)
    adjusted = np.empty_like(p)
    running = 0.0
    m = len(p)
    for rank, idx in enumerate(order):
        val = min(1.0, (m - rank) * p[idx])
        running = max(running, val)
        adjusted[idx] = running
    return adjusted.tolist()
