# Supply Chain Early Warning Demo

Discrete-time simulation of a small supply network demonstrating
measurable early detection of cascading overload before failure.

## Network
- 3 suppliers -> 4 warehouses -> 5 retail nodes
- Edges carry goods with transport delay and throughput limits

## Disruption
At t=150, warehouse W1 suffers a severe capacity drop.
Downstream retail nodes accumulate backlog.

## Detection
Rolling variance of total backlog rises before the backlog crosses
the failure threshold. Kendall tau trend of rolling variance
confirms sustained onset.

## Run
```
pip install -e .
python experiments/run_demo.py
```

## Dependencies
numpy, networkx, scipy, matplotlib
