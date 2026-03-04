"""
run_sim.py — Phase 1 simulation verification.

Checks:
1. Flat baseline pre-disruption (backlog ~ 0)
2. Cascade builds post-disruption
3. Failure threshold crossed within T
4. Cascade unfolds over sufficient steps for detection window

No detection logic. Detection layer added in Phase 2
after simulation dynamics are confirmed.
"""

import sys
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sc_sim.network    import build_network
from sc_sim.disruption import capacity_drop
from sc_sim.flow       import simulate

T                  = 400
T_DISRUPTION       = 150
DISRUPTION_NODE    = 'W1'
NEW_CAP            = 20.0
BACKLOG_THRESHOLD  = 200.0
RESULTS_DIR        = os.path.join(os.path.dirname(__file__), '..', 'results')

os.makedirs(RESULTS_DIR, exist_ok=True)


def main():
    G   = build_network()
    dfn = capacity_drop(DISRUPTION_NODE, NEW_CAP, T_DISRUPTION)
    backlog, _ = simulate(G, T=T, disruption_fn=dfn)

    # ── Verification checks ───────────────────────────────────
    pre_max   = backlog[:T_DISRUPTION].max()
    post_max  = backlog[T_DISRUPTION:].max()
    failure_t = next((i for i, v in enumerate(backlog)
                      if v >= BACKLOG_THRESHOLD), None)

    print()
    print("=" * 52)
    print("  Phase 1 — Simulation Verification")
    print("=" * 52)
    print(f"  Pre-disruption max backlog:   {pre_max:.2f}  (target: ~0)")
    print(f"  Post-disruption max backlog:  {post_max:.2f}")
    if failure_t is not None:
        print(f"  Failure threshold crossed:    t = {failure_t}")
        print(f"  Steps post-disruption:        {failure_t - T_DISRUPTION}")
    else:
        print(f"  Failure threshold not crossed within T={T}")
    print("=" * 52)
    print()

    # ── Plot ──────────────────────────────────────────────────
    t_axis = np.arange(T)
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(t_axis, backlog, color='steelblue', lw=1.5, label='Total backlog')
    ax.axvline(T_DISRUPTION, color='crimson', ls='--', alpha=0.7,
               label=f'Disruption (t={T_DISRUPTION})')
    if failure_t is not None:
        ax.axvline(failure_t, color='darkorange', ls=':', lw=2,
                   label=f'Failure threshold (t={failure_t})')
    ax.axhline(BACKLOG_THRESHOLD, color='darkorange', ls='--', alpha=0.3,
               label=f'Threshold ({BACKLOG_THRESHOLD})')
    ax.set_ylabel('Total System Backlog')
    ax.set_xlabel('Time Step')
    ax.set_title('Supply Chain Simulation — Phase 1 Verification')
    ax.legend(fontsize=8)
    plt.tight_layout()
    out = os.path.join(RESULTS_DIR, 'phase1_verification.png')
    plt.savefig(out, dpi=120)
    print(f"Plot saved to: {out}")


if __name__ == '__main__':
    main()