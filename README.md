# Supply Chain Early Warning Demo

Discrete-time simulation of a small supply network demonstrating
measurable early detection of cascading overload before failure.

The detection mechanism is grounded in **critical slowing down** — a
phenomenon from dynamical systems theory in which a system approaching
a bifurcation or threshold transition exhibits increasing variance and
autocorrelation in observable signals before the transition occurs.
This demo operationalizes that signal using rolling variance and
Kendall tau trend detection on total system backlog.

## Network

- 3 suppliers -> 4 warehouses -> 5 retail nodes
- Edges carry goods with transport delay and throughput limits
- Total nominal demand: 72 units/step
- Total nominal production: 120 units/step (surplus under normal conditions)
- W1 is the critical bottleneck node: serves R1 and R2 with 32 units/step capacity

## Disruption

At t=150, warehouse W1 suffers a severe capacity drop (200 -> 15).
Downstream retail nodes R1 and R2 begin accumulating backlog.
The cascade propagates as upstream suppliers continue producing
into a blocked network.

## Detection

Rolling variance of total backlog rises before the backlog crosses
the failure threshold. Kendall tau trend of rolling variance confirms
sustained monotonic onset rather than a transient spike.

The early warning signal precedes declared failure by a measurable
lead time — see output for the specific step count under default parameters.

### Threshold Basis

- `tau_threshold = 0.60` — tau >= 0.60 indicates >80% concordant pairs,
  reducing false positives from transient variance spikes. Tunable:
  lower values increase sensitivity, higher values improve specificity.
- `backlog_threshold = 200.0` — approximately 2.8x nominal demand,
  representing severe service degradation. Should be recalibrated
  if network parameters are changed.

## Run

```
pip install -e .
python experiments/run_demo.py
```

## Scaling Notes

The Kendall tau computation is O(T * window^2). At default parameters
(T=300, window=30) this is ~270,000 operations. For T > 5,000 or
window > 50, replace with a merge-sort based O(window log window)
implementation or use incremental variance updates.

## Dependencies

numpy, networkx, scipy, matplotlib

## Background

Critical slowing down as a precursor to system transitions is
documented across ecology, climate systems, and financial networks.
This demo applies the same detection principle to discrete supply
chain dynamics. Key reference:
Scheffer et al. (2009), "Early-warning signals for critical transitions",
Nature 461, 53-59. https://doi.org/10.1038/nature08227
