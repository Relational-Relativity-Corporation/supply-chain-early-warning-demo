"""
network.py — 3-4-5 supply network definition.

Topology:
    3 suppliers → 4 warehouses → 5 retail nodes

Baseline balance:
    Total demand     = 72 units/step  (R0:6, R1:20, R2:20, R3:20, R4:6)
    Total production = 75 units/step  (3 x 25/step)
    Net surplus      = 3 units/step — inventories stable pre-disruption

Throughput limits calibrated to steady-state flows:
    W0 receives 12.5/step → ships R0:6.0 + R1:6.5   = 12.5
    W1 receives 25.0/step → ships R1:13.5 + R2:11.5  = 25.0
    W2 receives 25.0/step → ships R2:11.5 + R3:13.5  = 25.0
    W3 receives 12.5/step → ships R3:6.5 + R4:6.0   = 12.5

W1 is the critical bottleneck: serves R1 and R2, absorbing
25 units/step. Capacity drop at W1 cascades to both downstream
retail nodes simultaneously.
"""

import networkx as nx


def build_network():
    G = nx.DiGraph()

    for i in range(3):
        G.add_node(f'S{i}', kind='supplier',
                   capacity=200.0, inventory=100.0,
                   demand=0.0, backlog=0.0,
                   production_rate=25.0)

    for i in range(4):
        G.add_node(f'W{i}', kind='warehouse',
                   capacity=200.0, inventory=100.0,
                   demand=0.0, backlog=0.0,
                   production_rate=0.0)

    demands = {'R0': 6.0, 'R1': 20.0, 'R2': 20.0, 'R3': 20.0, 'R4': 6.0}
    for i in range(5):
        nid = f'R{i}'
        G.add_node(nid, kind='retail',
                   capacity=80.0, inventory=40.0,
                   demand=demands[nid], backlog=0.0,
                   production_rate=0.0)

    # Supplier → Warehouse (delay=2)
    for u, v in [('S0','W0'), ('S0','W1'),
                 ('S1','W1'), ('S1','W2'),
                 ('S2','W2'), ('S2','W3')]:
        G.add_edge(u, v, throughput_limit=20.0, transport_delay=2)

    # Warehouse → Retail (delay=1, calibrated to steady-state)
    for u, v, tl in [
        ('W0','R0',  6.0), ('W0','R1',  6.5),
        ('W1','R1', 13.5), ('W1','R2', 11.5),
        ('W2','R2', 11.5), ('W2','R3', 13.5),
        ('W3','R3',  6.5), ('W3','R4',  6.0),
    ]:
        G.add_edge(u, v, throughput_limit=tl, transport_delay=1)

    return G