"""
disruption.py — Capacity drop injection.

Simulates warehouse damage or throughput reduction by clamping
node capacity and inventory to a new lower value at a declared
timestep.
"""


def capacity_drop(node: str, new_capacity: float, drop_time: int):
    """
    Returns a disruption function that drops node capacity at drop_time.

    Parameters
    ----------
    node         : node identifier in the network graph
    new_capacity : new capacity value post-disruption
    drop_time    : timestep at which disruption is applied
    """
    applied = [False]

    def fn(G, t: int):
        if t == drop_time and not applied[0]:
            G.nodes[node]['capacity']  = float(new_capacity)
            G.nodes[node]['inventory'] = min(
                G.nodes[node]['inventory'], float(new_capacity)
            )
            applied[0] = True

    return fn