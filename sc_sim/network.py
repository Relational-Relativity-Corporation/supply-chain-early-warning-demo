import networkx as nx


def build_network():
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

    for u, v in [('S0','W0'), ('S0','W1'),
                 ('S1','W1'), ('S1','W2'),
                 ('S2','W2'), ('S2','W3')]:
        G.add_edge(u, v, throughput_limit=25.0, transport_delay=2)

    for u, v, tl in [
        ('W0','R0',  8.0), ('W0','R1',  8.0),
        ('W1','R1', 16.0), ('W1','R2', 16.0),
        ('W2','R2',  8.0), ('W2','R3',  8.0),
        ('W3','R3', 16.0), ('W3','R4', 16.0),
    ]:
        G.add_edge(u, v, throughput_limit=tl, transport_delay=1)

    return G
