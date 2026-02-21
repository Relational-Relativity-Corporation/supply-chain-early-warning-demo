def capacity_drop(node, new_capacity, drop_time):
    applied = [False]

    def fn(G, t):
        if t == drop_time and not applied[0]:
            G.nodes[node]['capacity']  = float(new_capacity)
            G.nodes[node]['inventory'] = min(
                G.nodes[node]['inventory'], float(new_capacity)
            )
            applied[0] = True

    return fn
