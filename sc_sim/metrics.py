import numpy as np


def compute_trigger_times(backlog, tau_series,
                          tau_threshold=0.60,
                          backlog_threshold=200.0):
    """
    Identify early-warning and failure trigger times from simulation output.

    Parameters
    ----------
    backlog : array-like
        Total system backlog at each time step.
    tau_series : array-like
        Kendall tau trend of rolling variance at each time step.
    tau_threshold : float, default 0.60
        Minimum Kendall tau value to declare sustained instability onset.
        Basis: tau >= 0.60 indicates strong monotonic trend (>80% concordant
        pairs), reducing false positives from transient variance spikes.
        This threshold is tunable — lower values increase sensitivity at
        the cost of earlier false positives; higher values delay warning
        but improve specificity. Sensitivity analysis recommended for
        production use.
    backlog_threshold : float, default 200.0
        Total backlog level at which the system is declared failed.
        Basis: set at ~2.8x nominal demand (72 units/step) to represent
        a severe service degradation state rather than a transient spike.
        Should be recalibrated relative to total demand when network
        parameters are changed.

    Returns
    -------
    instability_time : int or None
        First time step where tau >= tau_threshold. None if not reached.
    failure_time : int or None
        First time step where backlog >= backlog_threshold. None if not reached.
    lead_time : int or None
        Steps between instability_time and failure_time. None if either
        trigger was not reached.
    """
    instability_time = next(
        (i for i, t in enumerate(tau_series)
         if not np.isnan(t) and t >= tau_threshold),
        None
    )
    failure_time = next(
        (i for i, b in enumerate(backlog) if b >= backlog_threshold),
        None
    )
    lead_time = (
        failure_time - instability_time
        if instability_time is not None and failure_time is not None
        else None
    )
    return instability_time, failure_time, lead_time
