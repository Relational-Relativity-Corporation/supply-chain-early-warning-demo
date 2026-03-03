"""
flow.py — Discrete-time supply chain simulation.

Retail serving and shipment dispatch use the bounded update operator:

    delta_M = clip(E - M, P_max)

where:
    E     = target state (demand + backlog for retail,
                          proportional share for dispatch)
    M     = current inventory
    P_max = throughput or serving limit

This replaces the multi-branch conditional logic of the original
implementation with a single relational operator that enforces
magnitude constraints continuously. The four-pass ordering is
preserved — structural correctness requires it regardless of
which operator governs each pass.
"""

import numpy as np


def _bounded_update(current, target, p_max):
    """
    Bounded update operator.

        delta_M = clip(target - current, p_max)

    Returns the signed update delta_M. The caller applies it.

    Parameters
    ----------
    current : float  Current state M.
    target  : float  Target state E.
    p_max   : float  Maximum permitted magnitude of update.

    Returns
    -------
    delta_M : float  Bounded update. Sign indicates direction.
    """
    return float(np.clip(target - current, -p_max, p_max))


def init_pipelines(G):
    return {
        (u, v): [0.0] * max(1, int(data.get('transport_delay', 1)))
        for u, v, data in G.edges(data=True)
    }


def _step(G, pipelines):
    """
    Advance simulation by one discrete time step.

    Pass ordering is mandatory:

      Pass 1 — Arrivals:   deliver pipeline heads to destination nodes
      Pass 2 — Production: suppliers generate inventory
      Pass 3 — Retail:     serve demand via bounded update operator
      Pass 4 — Shipments:  dispatch via bounded update operator

    The bounded update operator replaces conditional branching in
    passes 3 and 4. The relational structure — magnitude constraint
    between error and capacity — governs both.
    """
    nodes = G.nodes

    # ------------------------------------------------------------------
    # Pass 1 & 2 — Arrivals + Production
    # ------------------------------------------------------------------
    arrivals = {n: 0.0 for n in nodes}
    for (u, v), pipe in pipelines.items():
        arrivals[v] += pipe[0]

    for key in pipelines:
        pipelines[key] = pipelines[key][1:] + [0.0]

    for nid, data in nodes(data=True):
        inc = arrivals[nid]
        if data['kind'] == 'supplier':
            inc += data['production_rate']
        data['inventory'] = min(data['capacity'], data['inventory'] + inc)

    # ------------------------------------------------------------------
    # Pass 3 — Retail Serving via bounded update operator
    #
    # Target E = backlog + demand (full obligation)
    # Current M = inventory
    # P_max = inventory (can only serve what exists)
    #
    # delta_M = clip(E - M, P_max) gives maximum serving within
    # available inventory. Backlog is reduced by what was served
    # beyond current demand.
    # ------------------------------------------------------------------
    for nid, data in nodes(data=True):
        if data['kind'] != 'retail':
            continue
        obligation = data['backlog'] + data['demand']
        delta_M    = _bounded_update(0.0, obligation, data['inventory'])
        served     = abs(delta_M)
        bl_resolved = min(served, data['backlog'])
        data['inventory'] -= served
        data['backlog']   -= bl_resolved
        data['backlog']   += data['demand'] - (served - bl_resolved)

    # ------------------------------------------------------------------
    # Pass 4 — Shipments via bounded update operator
    #
    # For each downstream edge, target share is proportional to
    # throughput limit. P_max = throughput_limit per edge.
    # delta_M = clip(share - 0, throughput_limit) = min(share, tl)
    # which is exactly the relational dispatch constraint.
    # ------------------------------------------------------------------
    for nid, data in nodes(data=True):
        succ = list(G.successors(nid))
        if not succ:
            continue
        total_tl = sum(G.edges[nid, v]['throughput_limit'] for v in succ)
        if total_tl <= 0:
            raise ValueError(
                f"Node {nid} has total downstream throughput_limit={total_tl}. "
                "Shipment dispatch requires at least one edge with positive throughput."
            )
        avail = data['inventory']
        shipments = {}
        for v in succ:
            tl    = G.edges[nid, v]['throughput_limit']
            share = avail * (tl / total_tl)
            delta = _bounded_update(0.0, share, tl)
            shipments[v] = abs(delta)
        data['inventory'] -= sum(shipments.values())
        for v, amt in shipments.items():
            pipelines[(nid, v)][-1] += amt

    return sum(d['backlog'] for _, d in nodes(data=True))


def simulate(G, T=300, disruption_fn=None):
    """
    Run simulation for T steps, recording regime state each step.

    Returns
    -------
    backlog     : np.ndarray shape (T,)
    G_states    : list of (G_snapshot, pipelines_snapshot) per step
                  for regime indicator computation.
    """
    import copy
    pipelines = init_pipelines(G)
    backlog   = np.zeros(T)
    G_states  = []
    for t in range(T):
        if disruption_fn is not None:
            disruption_fn(G, t)
        G_states.append((copy.deepcopy(G), copy.deepcopy(pipelines)))
        backlog[t] = _step(G, pipelines)
    return backlog, G_states
