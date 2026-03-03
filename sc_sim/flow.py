"""
flow.py — Discrete-time supply chain simulation.

Retail serving and shipment dispatch use the bounded update operator:

    delta_M = clip(E - M, P_max)

Pipelines are pre-filled with steady-state flow values so the
simulation starts in equilibrium rather than cold. This eliminates
the startup transient where retail inventory depletes before the
first pipeline deliveries arrive.
"""

import numpy as np


def _bounded_update(current, target, p_max):
    """
    Bounded update operator.

        delta_M = clip(target - current, p_max)

    Returns the signed update delta_M.
    """
    return float(np.clip(target - current, -p_max, p_max))


def init_pipelines(G):
    """
    Initialise pipelines pre-filled with steady-state flow.

    Each pipeline slot is filled with the edge throughput_limit
    divided by the number of delay slots, approximating the
    steady-state per-slot flow. This starts the simulation in
    equilibrium and eliminates the cold-start transient.
    """
    pipelines = {}
    for u, v, data in G.edges(data=True):
        delay     = max(1, int(data.get('transport_delay', 1)))
        tl        = data['throughput_limit']
        # Steady-state fill: each slot carries tl / delay units
        # so total in-transit equals throughput_limit at t=0
        fill      = tl / delay
        pipelines[(u, v)] = [fill] * delay
    return pipelines


def _step(G, pipelines):
    """
    Advance simulation by one discrete time step.

    Pass ordering is mandatory:
      Pass 1 — Arrivals + Production
      Pass 2 — Retail serving via bounded update operator
      Pass 3 — Shipments via bounded update operator
    """
    nodes = G.nodes

    # ------------------------------------------------------------------
    # Pass 1 — Arrivals + Production
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
    # Pass 2 — Retail Serving via bounded update operator
    # ------------------------------------------------------------------
    for nid, data in nodes(data=True):
        if data['kind'] != 'retail':
            continue
        obligation  = data['backlog'] + data['demand']
        delta_M     = _bounded_update(0.0, obligation, data['inventory'])
        served      = abs(delta_M)
        bl_resolved = min(served, data['backlog'])
        data['inventory'] -= served
        data['backlog']   -= bl_resolved
        data['backlog']   += data['demand'] - (served - bl_resolved)

    # ------------------------------------------------------------------
    # Pass 3 — Shipments via bounded update operator
    # ------------------------------------------------------------------
    for nid, data in nodes(data=True):
        succ = list(G.successors(nid))
        if not succ:
            continue
        total_tl = sum(G.edges[nid, v]['throughput_limit'] for v in succ)
        if total_tl <= 0:
            raise ValueError(
                f"Node {nid} has total downstream throughput_limit={total_tl}."
            )
        avail     = data['inventory']
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
    Run simulation for T steps recording regime state each step.

    Returns
    -------
    backlog  : np.ndarray shape (T,)
    G_states : list of (G_snapshot, pipelines_snapshot) per step
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
