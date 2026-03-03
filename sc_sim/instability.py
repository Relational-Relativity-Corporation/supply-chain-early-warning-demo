"""
instability.py — Relational regime detection.

Replaces rolling variance and Kendall tau with the invariant
regime indicator derived from relational magnitudes:

    D_max = sup over edges of (flow / throughput_limit)
            Maximum relational strain in the network.

    P_max = inf over nodes of (spare_capacity / capacity)
            Minimum normalized adaptive capacity available.

    I = P_max - D_max

Regimes:
    I > 0  Stable      — plasticity exceeds strain
    I = 0  Critical    — boundary condition
    I < 0  Divergent   — strain exceeds available plasticity

This gives early warning by structural necessity: I crosses zero
before backlog accumulates to failure threshold, because relational
strain saturates capacity before downstream effects are observable.

No window parameters. No statistical thresholds. No tuning.
The mathematics determines the regime directly from network state.
"""

import numpy as np


def compute_regime_indicator(G, pipelines):
    """
    Compute the scalar regime indicator I = P_max - D_max
    from current network state.

    Parameters
    ----------
    G : networkx.DiGraph
        Network graph with current node inventories and capacities.
    pipelines : dict
        Edge pipeline queues as produced by flow.init_pipelines.

    Returns
    -------
    I : float
        Regime indicator. Positive = stable, zero = critical,
        negative = divergent.
    D_max : float
        Maximum relational strain across all edges.
    P_max : float
        Minimum normalized spare capacity across all nodes.
    """
    # D_max: maximum strain = flow-in-transit / throughput_limit per edge
    strains = []
    for (u, v), pipe in pipelines.items():
        tl = G.edges[u, v]['throughput_limit']
        if tl <= 0:
            raise ValueError(
                f"Edge ({u}, {v}) has throughput_limit={tl}. "
                "Zero or negative throughput limits are not permitted — "
                "strain is undefined on a zero-capacity edge."
            )
        in_transit = sum(pipe)
        strains.append(in_transit / tl)
    D_max = max(strains) if strains else 0.0

    # P_max: minimum normalized spare capacity across all nodes
    spare = []
    for nid, data in G.nodes(data=True):
        cap = data['capacity']
        inv = data['inventory']
        if cap > 0:
            spare.append((cap - inv) / cap)
    P_max = min(spare) if spare else 0.0

    I = P_max - D_max
    return I, D_max, P_max


def regime_series(G_states):
    """
    Compute regime indicator series over a recorded simulation run.

    Parameters
    ----------
    G_states : list of (G, pipelines) tuples recorded per timestep.

    Returns
    -------
    I_series : np.ndarray of shape (T,)
    D_series : np.ndarray of shape (T,)
    P_series : np.ndarray of shape (T,)
    """
    results = [compute_regime_indicator(G, p) for G, p in G_states]
    I_series = np.array([r[0] for r in results])
    D_series = np.array([r[1] for r in results])
    P_series = np.array([r[2] for r in results])
    return I_series, D_series, P_series


def compute_trigger_times(backlog, I_series,
                          backlog_threshold=200.0):
    """
    Identify early-warning and failure trigger times.

    Early warning fires when I first crosses zero (divergent regime).
    Failure fires when backlog crosses backlog_threshold.

    Parameters
    ----------
    backlog : np.ndarray
    I_series : np.ndarray
        Regime indicator series. Negative values indicate divergence.
    backlog_threshold : float

    Returns
    -------
    instability_time : int or None
    failure_time : int or None
    lead_time : int or None
    """
    instability_time = next(
        (i for i, v in enumerate(I_series) if v < 0.0),
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
