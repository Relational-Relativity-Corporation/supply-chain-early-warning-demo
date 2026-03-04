"""
instability.py — Relational regime detection.

Regime indicator:

    I = P_max - D_max

    D_max = max over edges of (last dispatched / throughput_limit)
            Measured using pipe[-1], the most recently dispatched
            quantity in the pipeline. G_states snapshots are taken
            before _step runs, so pipe[-1] is the dispatch from the
            immediately preceding step — the correct index for current
            dispatch pressure. pipe[0] would measure what arrives this
            step, which on a delay-2 edge is dispatch from two steps
            ago; using it would introduce a lag and understate strain
            on supplier->warehouse edges.

    P_max = min over nodes of (spare_capacity / capacity)
            Minimum normalised spare capacity across all nodes.
            min is intentional: it identifies the binding constraint —
            the node whose saturation limits what the network can absorb
            next. Mean or sum spare capacity would allow a fully
            saturated bottleneck to be masked by slack elsewhere,
            producing false negatives. If the tightest node is at zero
            spare, the network cannot absorb additional strain regardless
            of headroom at other nodes.

Regimes:
    I > 0  Stable    — plasticity exceeds strain
    I = 0  Critical  — boundary condition
    I < 0  Divergent — strain exceeds available plasticity

This is an instance of the invariant relational operator:

    delta_M = clip(E - M, P_max)

The stability boundary I = 0 is where the bounded update
operator can no longer absorb incoming strain.

No statistical inference, no sliding windows, no inference model
parameters. The failure threshold (backlog_threshold) defines your
operating constraint; the mathematics determines whether the network
can meet it.
"""

import numpy as np


def compute_regime_indicator(G, pipelines) -> tuple:
    """
    Compute scalar regime indicator I = P_max - D_max.

    D_max uses pipe[-1] (most recent dispatch) — see module docstring
    for snapshot timing rationale.

    P_max uses min(spare) — see module docstring for binding-constraint
    rationale.

    Returns
    -------
    I     : float — regime indicator
    D_max : float — maximum edge strain (current dispatch pressure)
    P_max : float — minimum node plasticity (binding constraint)
    """
    strains = []
    for (u, v), pipe in pipelines.items():
        tl = G.edges[u, v]['throughput_limit']
        if tl <= 0:
            raise ValueError(f"Edge ({u},{v}) throughput_limit={tl} invalid.")
        strains.append(pipe[-1] / tl)
    D_max = max(strains) if strains else 0.0

    spare = []
    for nid, data in G.nodes(data=True):
        cap = data['capacity']
        if cap > 0:
            spare.append((cap - data['inventory']) / cap)
    P_max = min(spare) if spare else 0.0

    return P_max - D_max, D_max, P_max


def regime_series(G_states) -> tuple:
    """
    Compute regime indicator series over a recorded simulation run.

    Parameters
    ----------
    G_states : list of (G, pipelines) tuples recorded per timestep

    Returns
    -------
    I_series : np.ndarray (T,)
    D_series : np.ndarray (T,)
    P_series : np.ndarray (T,)
    """
    results  = [compute_regime_indicator(G, p) for G, p in G_states]
    I_series = np.array([r[0] for r in results])
    D_series = np.array([r[1] for r in results])
    P_series = np.array([r[2] for r in results])
    return I_series, D_series, P_series


def compute_trigger_times(backlog, I_series,
                          backlog_threshold: float = 200.0) -> tuple:
    """
    Identify early-warning and failure trigger times.

    Early warning: first timestep where I < 0 (divergent regime).
    Failure: first timestep where total backlog >= backlog_threshold.

    backlog_threshold is a user-defined operating constraint, not an
    inference model parameter. It defines what counts as failure for
    your system; it does not tune the detection mechanism.
    """
    instability_time = next(
        (i for i, v in enumerate(I_series) if v < 0.0), None
    )
    failure_time = next(
        (i for i, b in enumerate(backlog) if b >= backlog_threshold), None
    )
    lead_time = (
        failure_time - instability_time
        if instability_time is not None and failure_time is not None
        else None
    )
    return instability_time, failure_time, lead_time