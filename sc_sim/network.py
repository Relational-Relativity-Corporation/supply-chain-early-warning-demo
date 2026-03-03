import networkx as nx


def build_network():
    """
    Build the 3-4-5 supply network.

    Production is balanced with demand so the network reaches
    stable equilibrium with meaningful spare capacity:

        Total demand    : 72 units/step (across 5 retail nodes)
        Total production: 75 units/step (3 suppliers x 25/step)

    This ensures I = P_max - D_max > 0 under normal operation.
    Under disruption, capacity collapse forces backlog accumulation,
    nodes fill, P_max drops, D_max rises, and I crosses zero —
    providing genuine early warning before failure threshold.

    Throughput limits are set at 1.5x nominal steady-state flow
    to provide headroom while still allowing strain to rise under
    disruption.
    """
    G = nx.DiGraph()

    for i in range(3):
        G.add_node(f'S{i}', kind='supplier',
                   capacity=200.0, inventory=50.0,
                   demand=0.0, backlog=0.0,
                   production_rate=25.0)

    for i in range(4):
        G.add_node(f'W{i}', kind='warehouse',
                   capacity=200.0, inventory=50.0,
                   demand=0.0, backlog=0.0)

    for i in range(5):
        G.add_node(f'R{i}', kind='retail',
                   capacity=80.0, inventory=20.0,
                   demand=0.0, backlog=0.0)

    for nid, d in [('R0', 6.0), ('R1', 20.0), ('R2', 20.0),
                   ('R3', 20.0), ('R4', 6.0)]:
        G.nodes[nid]['demand'] = d

    # Supplier -> Warehouse: nominal ~12/step, tl = 20
    for u, v in [('S0','W0'), ('S0','W1'),
                 ('S1','W1'), ('S1','W2'),
                 ('S2','W2'), ('S2','W3')]:
        G.add_edge(u, v, throughput_limit=20.0, transport_delay=2)

    # Warehouse -> Retail
    # High-demand routes nominal ~10/step: tl = 15
    # Low-demand routes  nominal  ~3/step: tl = 8
    for u, v, tl in [
        ('W0','R0',  8.0), ('W0','R1',  8.0),
        ('W1','R1', 15.0), ('W1','R2', 15.0),
        ('W2','R2',  8.0), ('W2','R3',  8.0),
        ('W3','R3', 15.0), ('W3','R4', 15.0),
    ]:
        G.add_edge(u, v, throughput_limit=tl, transport_delay=1)

    return G
