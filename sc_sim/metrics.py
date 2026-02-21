import numpy as np


def compute_trigger_times(backlog, tau_series,
                          tau_threshold=0.60,
                          backlog_threshold=200.0):
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
