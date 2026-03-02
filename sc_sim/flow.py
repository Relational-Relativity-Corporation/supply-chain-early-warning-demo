import numpy as np


def init_pipelines(G):
    return {
        (u, v): [0.0] * max(1, int(data.get('transport_delay', 1)))
        for u, v, data in G.edges(data=True)
    }


def _step(G, pipelines):
    """
    Advance simulation by one discrete time step.

    Structural pass ordering is mandatory and must not be collapsed:

      Pass 1 — Arrivals:   deliver pipeline heads to destination nodes
      Pass 2 — Production: suppliers generate inventory
      Pass 3 — Retail:     serve demand and accumulate backlog
      Pass 4 — Shipments:  upstream nodes dispatch to downstream pipes

    Collapsing any two passes into one loop produces incorrect dynamics
    because downstream inventory must be fully updated before shipments
    are calculated, and backlog must be resolved before new shipments
    are dispatched.
    """
    nodes = G.nodes

    # ------------------------------------------------------------------
    # Pass 1 & 2 — Arrivals + Production
    # Deliver pipeline heads; suppliers add production to inventory.
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
    # Pass 3 — Retail Serving
    # Resolve backlog and current demand against available inventory.
    # Backlog is served first (FIFO priority).
    # Non-negativity of backlog is guaranteed:
    #   served <= inventory, bl_srv <= backlog, dm_srv <= demand
    # ------------------------------------------------------------------
    for nid, data in nodes(data=True):
        if data['kind'] != 'retail':
            continue
        served   = min(data['inventory'], data['demand'] + data['backlog'])
        bl_srv   = min(served, data['backlog'])
        dm_srv   = min(served - bl_srv, data['demand'])
        data['inventory'] -= bl_srv + dm_srv
        data['backlog']   += data['demand'] - dm_srv
        data['backlog']   -= bl_srv

    # ------------------------------------------------------------------
    # Pass 4 — Shipments
    # Each non-leaf node dispatches inventory proportionally to
    # downstream throughput limits.
    # sum(shipments) <= avail is guaranteed by proportional allocation,
    # so inventory remains non-negative.
    # ------------------------------------------------------------------
    for nid, data in nodes(data=True):
        succ = list(G.successors(nid))
        if not succ:
            continue
        total_tl = sum(G.edges[nid, v]['throughput_limit'] for v in succ)
        avail    = data['inventory']
        shipments = {
            v: min(avail * (G.edges[nid, v]['throughput_limit'] / total_tl),
                   G.edges[nid, v]['throughput_limit'])
            for v in succ
        }
        data['inventory'] -= sum(shipments.values())
        for v, amt in shipments.items():
            pipelines[(nid, v)][-1] += amt

    return sum(d['backlog'] for _, d in nodes(data=True))


def simulate(G, T=300, disruption_fn=None):
    pipelines = init_pipelines(G)
    backlog   = np.zeros(T)
    for t in range(T):
        if disruption_fn is not None:
            disruption_fn(G, t)
        backlog[t] = _step(G, pipelines)
    return backlog
