"""
metrics.py — Trigger time computation.

compute_trigger_times returns the first timestep at which:
  - instability_t : ABCRE field signal exceeds declared signal_threshold
  - failure_t     : total backlog exceeds declared backlog_threshold
  - lead_time     : failure_t - instability_t  (None if either is None)

signal_threshold is declared over the L2 norm of the C output field.
Max possible norm = sqrt(n_nodes). Baseline near 0 at equilibrium.

backlog_threshold is declared over total system backlog.
"""

import numpy as np


def compute_trigger_times(
    backlog:           np.ndarray,
    signal:            np.ndarray,
    signal_threshold:  float,
    backlog_threshold: float,
) -> tuple:
    """
    Parameters
    ----------
    backlog           : total system backlog array, shape (T,)
    signal            : ABCRE field signal array, shape (T,)
    signal_threshold  : norm value above which instability is declared
    backlog_threshold : backlog value above which failure is declared

    Returns
    -------
    instability_t : int or None
    failure_t     : int or None
    lead_time     : int or None
    """
    instability_t = next(
        (i for i, v in enumerate(signal) if v >= signal_threshold),
        None
    )

    failure_t = next(
        (i for i, v in enumerate(backlog) if v >= backlog_threshold),
        None
    )

    lead_time = (
        failure_t - instability_t
        if instability_t is not None and failure_t is not None
        else None
    )

    return instability_t, failure_t, lead_time