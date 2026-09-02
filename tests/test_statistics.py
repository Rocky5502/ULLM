import math

from ullm.statistics import cluster_bootstrap, holm_adjust


def test_cluster_bootstrap_is_seed_reproducible():
    values = [0.0, 1.0, 0.0, 1.0]
    clusters = ["a", "a", "b", "b"]
    a = cluster_bootstrap(values, clusters, n_boot=100, seed=7)
    b = cluster_bootstrap(values, clusters, n_boot=100, seed=7)
    assert a == b
    point, low, high = a
    assert math.isclose(point, 0.5)
    assert low <= point <= high


def test_holm_adjust_is_monotone_in_sorted_pvalues():
    raw = [0.001, 0.02, 0.04]
    adjusted = holm_adjust(raw)
    assert all(0.0 <= p <= 1.0 for p in adjusted)
    assert adjusted[0] <= adjusted[1] <= adjusted[2]
    assert adjusted[0] >= raw[0]
