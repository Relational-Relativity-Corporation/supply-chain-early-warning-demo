import numpy as np


def init_pipelines(G):
    return {
        (u, v): [0.0] * max(1, int(data.get('transport_delay', 1)))
        for u, v, data in G.edges(data=True)
    }


def _step(G, pipelines):
    nodes = G.nodes

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

    for nid, data in nodes(data=True):
        if data['kind'] != 'retail':
            continue
        served   = min(data['inventory'], data['demand'] + data['backlog'])
        bl_srv   = min(served, data['backlog'])
        dm_srv   = min(served - bl_srv, data['demand'])
        data['inventory'] -= bl_srv + dm_srv
        data['backlog']   += data['demand'] - dm_srv
        data['backlog']   -= bl_srv

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
