"""
flow.py — Discrete-time supply chain simulation.

Pipeline delay model:

    pipeline_ij(t+1, d) = pipeline_ij(t, d-1)
    arrival_j          += pipeline_ij(t, 0)

Three-pass step ordering (causally necessary):

    Pass 1 — Arrivals + Production
    Pass 2 — Retail serving
    Pass 3 — Shipment dispatch

Pipelines pre-filled with steady-state flow to eliminate
cold-start transient.
"""

import copy
import numpy as np


def init_pipelines(G) -> dict:
    """Pre-fill pipelines with steady-state flow."""
    pipelines = {}
    for u, v, data in G.edges(data=True):
        delay            = max(1, int(data.get('transport_delay', 1)))
        tl               = data['throughput_limit']
        fill             = tl / delay
        pipelines[(u,v)] = [fill] * delay
    return pipelines


def _step(G, pipelines) -> float:
    nodes = G.nodes

    # ── Pass 1: Arrivals + Production ────────────────────────
    arrivals = {n: 0.0 for n in nodes}
    for (u, v), pipe in pipelines.items():
        arrivals[v] += pipe[0]

    for key in pipelines:
        pipelines[key] = pipelines[key][1:] + [0.0]

    for nid, data in nodes(data=True):
        inc = arrivals[nid] + data.get('production_rate', 0.0)
        data['inventory'] = min(data['capacity'], data['inventory'] + inc)

    # ── Pass 2: Retail Serving ────────────────────────────────
    for nid, data in nodes(data=True):
        if data['kind'] != 'retail':
            continue
        obligation  = data['backlog'] + data['demand']
        served      = min(obligation, data['inventory'])
        bl_resolved = min(served, data['backlog'])
        data['inventory'] -= served
        data['backlog']   -= bl_resolved
        data['backlog']   += data['demand'] - (served - bl_resolved)

    # ── Pass 3: Shipment Dispatch ─────────────────────────────
    for nid, data in nodes(data=True):
        succ = list(G.successors(nid))
        if not succ:
            continue
        total_tl = sum(G.edges[nid, v]['throughput_limit'] for v in succ)
        avail    = data['inventory']
        shipped  = 0.0
        for v in succ:
            tl         = G.edges[nid, v]['throughput_limit']
            share      = avail * (tl / total_tl)
            dispatched = min(share, tl)
            pipelines[(nid, v)][-1] += dispatched
            shipped += dispatched
        data['inventory'] -= shipped

    return sum(d['backlog'] for _, d in nodes(data=True))


def simulate(G, T: int = 400, disruption_fn=None) -> tuple:
    """
    Run simulation for T timesteps.

    Returns
    -------
    backlog  : np.ndarray (T,) — total system backlog per step
    G_states : list of (G_snapshot, pipelines_snapshot) per step
    """
    pipelines = init_pipelines(G)
    backlog   = np.zeros(T)
    G_states  = []

    for t in range(T):
        if disruption_fn is not None:
            disruption_fn(G, t)
        G_states.append((copy.deepcopy(G), copy.deepcopy(pipelines)))
        backlog[t] = _step(G, pipelines)

    return backlog, G_states