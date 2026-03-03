import networkx as nx


def build_network():
    """
    Build the 3-4-5 supply network.

    Throughput limits are set at 1.5x nominal flow to provide
    meaningful headroom. Under normal operating conditions edges
    run at ~67% capacity, giving D_max < P_max and I > 0 (stable).

    Only under disruption — when capacity drops force backlog
    accumulation and pipelines fill beyond nominal flow — does
    strain rise toward 1.0, causing I to cross zero and signal
    the divergent regime.

    Nominal flows (per edge at steady state):
        Supplier -> Warehouse : ~25 units/step  -> tl = 38
        Warehouse -> Retail (high demand) : ~16 -> tl = 24
        Warehouse -> Retail (low demand)  :  ~8 -> tl = 12
    """
    G = nx.DiGraph()

    for i in range(3):
        G.add_node(f'S{i}', kind='supplier',
                   capacity=200.0, inventory=150.0,
                   demand=0.0, backlog=0.0,
                   production_rate=40.0)

    for i in range(4):
        G.add_node(f'W{i}', kind='warehouse',
                   capacity=200.0, inventory=120.0,
                   demand=0.0, backlog=0.0)

    for i in range(5):
        G.add_node(f'R{i}', kind='retail',
                   capacity=80.0, inventory=40.0,
                   demand=0.0, backlog=0.0)

    for nid, d in [('R0', 6.0), ('R1', 20.0), ('R2', 20.0),
                   ('R3', 20.0), ('R4', 6.0)]:
        G.nodes[nid]['demand'] = d

    # Supplier -> Warehouse edges
    # Nominal flow ~25/step, tl = 38 (1.5x headroom)
    for u, v in [('S0','W0'), ('S0','W1'),
                 ('S1','W1'), ('S1','W2'),
                 ('S2','W2'), ('S2','W3')]:
        G.add_edge(u, v, throughput_limit=38.0, transport_delay=2)

    # Warehouse -> Retail edges
    # High-demand routes (nominal ~16/step): tl = 24
    # Low-demand routes  (nominal  ~8/step): tl = 12
    for u, v, tl in [
        ('W0','R0', 12.0), ('W0','R1', 12.0),
        ('W1','R1', 24.0), ('W1','R2', 24.0),
        ('W2','R2', 12.0), ('W2','R3', 12.0),
        ('W3','R3', 24.0), ('W3','R4', 24.0),
    ]:
        G.add_edge(u, v, throughput_limit=tl, transport_delay=1)

    return G
