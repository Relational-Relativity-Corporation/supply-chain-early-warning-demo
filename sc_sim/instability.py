import numpy as np
from scipy import stats


def rolling_variance(series, window=20):
    n  = len(series)
    rv = np.full(n, np.nan, dtype=float)
    for i in range(window - 1, n):
        rv[i] = np.var(series[i - window + 1: i + 1], dtype=float)
    return rv


def kendall_tau_trend(series, window=30):
    n   = len(series)
    tau = np.full(n, np.nan, dtype=float)
    x   = np.arange(window, dtype=float)
    for i in range(window - 1, n):
        seg = series[i - window + 1: i + 1]
        if np.any(np.isnan(seg)):
            continue
        tau[i], _ = stats.kendalltau(x, seg.astype(float))
    return tau
