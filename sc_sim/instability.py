import numpy as np
from scipy import stats


def rolling_variance(series, window=20):
    """
    Compute rolling population variance over a fixed window.

    Population variance (/ window) is used rather than sample variance
    (/ window-1) because the window is treated as a complete observation
    set for signal detection purposes, not a sample estimator.

    Complexity: O(T * window). Suitable for T <= 10,000 and window <= 100.
    For larger scales, consider incremental variance updates:
        var_new = var_old + (x_new - x_old)(x_new - mean_new + x_old - mean_old) / window
    """
    n  = len(series)
    rv = np.full(n, np.nan, dtype=float)
    for i in range(window - 1, n):
        rv[i] = np.var(series[i - window + 1: i + 1], dtype=float)
    return rv


def kendall_tau_trend(series, window=30):
    """
    Compute rolling Kendall tau rank correlation against a linear index.

    Kendall tau measures the monotonic trend of rolling variance within
    each window. A sustained positive tau indicates the variance is
    consistently rising — the core early-warning signal.

    tau = +1.0  all pairwise comparisons concordant (pure upward trend)
    tau = -1.0  all pairwise comparisons discordant (pure downward trend)
    tau =  0.0  no monotonic trend

    Complexity: O(T * window^2). At default T=300, window=30 this is
    approximately 270,000 operations — acceptable. For T > 5,000 or
    window > 50, replace the inner loop with scipy.stats.kendalltau
    on sorted ranks or use a merge-sort based O(window log window)
    implementation.
    """
    n   = len(series)
    tau = np.full(n, np.nan, dtype=float)
    x   = np.arange(window, dtype=float)
    for i in range(window - 1, n):
        seg = series[i - window + 1: i + 1]
        if np.any(np.isnan(seg)):
            continue
        tau[i], _ = stats.kendalltau(x, seg.astype(float))
    return tau
