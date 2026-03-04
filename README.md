# Supply Chain Early Warning Demo

Discrete-time simulation of a small supply network demonstrating
structural early detection of cascading overload before failure.

## Detection Mechanism

The regime indicator:

```
I = P_max - D_max
```

- `D_max` — maximum edge strain: most recent dispatch / throughput limit
- `P_max` — minimum node plasticity: spare capacity / capacity
  (min is intentional — it identifies the binding constraint, not mean
  network elasticity. A saturated bottleneck limits absorption regardless
  of slack elsewhere.)
- `I > 0` stable, `I = 0` critical, `I < 0` divergent

When I crosses zero the network structurally cannot absorb incoming
strain. This crossing precedes observable backlog accumulation by a
measurable lead time.

No statistical inference, no sliding windows, no inference model
parameters. The failure threshold defines your operating constraint;
the mathematics determines whether the network can meet it.

## Network

- 3 suppliers, 4 warehouses, 5 retail nodes
- Total demand: 72 units/step. Total production: 75 units/step
- Throughput limits calibrated to steady-state flows
- W1 is the critical bottleneck: serves R1 and R2 (40 units/step demand)

## Disruption

At t=150, warehouse W1 capacity drops from 200 to 20 units.
Downstream retail nodes R1 and R2 begin accumulating backlog.
Cascade propagates as upstream suppliers continue producing
into a blocked network.

## Results

Run to see exact lead time. The regime indicator I crosses zero
before the backlog failure threshold is reached, providing structural
early warning without an inference model.

The failure threshold (default 200 units) defines what counts as
failure for your system. It is not a detection parameter — the regime
crossing is determined entirely by network structure and disruption
magnitude.

## Run

```
pip install -e .
python experiments/run_demo.py
```

Results saved to `results/regime_early_warning.png`.

## Mathematical Background

The regime indicator is an instance of the invariant relational operator:

```
delta_M = clip(E - M, P_max)
```

The stability boundary I = 0 is where the bounded update operator
can no longer absorb incoming strain. This is the same structure
that governs the bounded plasticity simulation — the supply chain
is one domain instantiation of a domain-independent relational invariant.

No inference model parameters. The failure threshold defines your
operating constraint; the mathematics determines the regime.

See also:
- [Bounded Plasticity Simulation](https://github.com/Relational-Relativity-Corporation/bounded-plasticity-simulation)
- [Robotics Instability Detection — Relational](https://github.com/Relational-Relativity-Corporation/robotics-instability-detection-relational)

## Dependencies

numpy, networkx, matplotlib

## Repository Structure

```
supply-chain-early-warning-demo/
├── experiments/
│   └── run_demo.py       — simulation and plot script
├── notebooks/
│   └── demo.ipynb        — interactive walkthrough with sensitivity analysis
├── sc_sim/
│   ├── network.py        — 3-4-5 supply network definition
│   ├── flow.py           — simulation loop with bounded update operator
│   ├── disruption.py     — capacity drop injection
│   └── instability.py    — regime indicator I = P_max - D_max
├── results/              — generated plots (gitignored)
├── pyproject.toml
└── README.md
```