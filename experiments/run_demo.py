"""
run_demo.py — Supply Chain Early Warning Demo

Demonstrates relational regime detection on a 3-4-5 supply network.
At t=150, warehouse W1 suffers a capacity drop from 200 to 20 units.
The regime indicator I = P_max - D_max crosses zero before backlog
reaches the failure threshold, providing structural early warning
without statistical inference or tuning parameters.
"""

import sys
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sc_sim.network     import build_network
from sc_sim.disruption  import capacity_drop
from sc_sim.flow        import simulate
from sc_sim.instability import regime_series, compute_trigger_times

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
    backlog, G_states = simulate(G, T=T, disruption_fn=dfn)

    I_series, D_series, P_series = regime_series(G_states)
    instability_t, failure_t, lead_time = compute_trigger_times(
        backlog, I_series, backlog_threshold=BACKLOG_THRESHOLD
    )

    print()
    print("=" * 52)
    print("  Supply Chain Early Warning — Regime Indicator")
    print("=" * 52)
    print(f"  Disruption applied:    t = {T_DISRUPTION}")
    if instability_t is not None:
        print(f"  Regime I < 0 at:       t = {instability_t}  (divergent)")
    else:
        print("  Regime I < 0:          not reached")
    if failure_t is not None:
        print(f"  Failure threshold:     t = {failure_t}")
    else:
        print("  Failure threshold:     not reached")
    if lead_time is not None:
        print(f"  Lead time:             {lead_time} steps before failure")
    else:
        print("  Lead time:             N/A")
    print("=" * 52)
    print()

    t_axis = np.arange(T)
    fig, axes = plt.subplots(4, 1, figsize=(11, 13), sharex=True)
    fig.suptitle(
        'Supply Chain Early Warning — Relational Regime Indicator\n'
        r'$I = P_{\max} - D_{\max}$   '
        r'$I > 0$ stable   $I = 0$ critical   $I < 0$ divergent',
        fontsize=12
    )

    ax = axes[0]
    ax.plot(t_axis, backlog, color='steelblue', lw=1.5, label='Total backlog')
    ax.axhline(BACKLOG_THRESHOLD, color='crimson', lw=1.2, ls='--',
               label=f'Failure threshold ({BACKLOG_THRESHOLD})')
    ax.axvline(T_DISRUPTION, color='orange', lw=1.0, ls=':',
               label=f'Disruption t={T_DISRUPTION}')
    if failure_t is not None:
        ax.axvline(failure_t, color='crimson', lw=1.0, ls=':',
                   label=f'Failure t={failure_t}')
    ax.set_ylabel('Backlog (units)')
    ax.legend(fontsize=8, loc='upper left')
    ax.set_title('Total System Backlog', fontsize=10)

    ax = axes[1]
    ax.plot(t_axis, I_series, color='darkorchid', lw=1.5,
            label='I = P_max - D_max')
    ax.axhline(0.0, color='black', lw=0.8, ls='--',
               label='Critical boundary (I = 0)')
    ax.axvline(T_DISRUPTION, color='orange', lw=1.0, ls=':')
    if instability_t is not None:
        ax.axvline(instability_t, color='darkorchid', lw=1.0, ls=':',
                   label=f'I < 0 at t={instability_t}')
    if failure_t is not None:
        ax.axvline(failure_t, color='crimson', lw=1.0, ls=':')
    ax.fill_between(t_axis, I_series, 0, where=(I_series < 0),
                    alpha=0.15, color='crimson', label='Divergent region')
    ax.fill_between(t_axis, I_series, 0, where=(I_series >= 0),
                    alpha=0.10, color='green',  label='Stable region')
    ax.set_ylabel('I (regime indicator)')
    ax.legend(fontsize=8, loc='upper left')
    ax.set_title('Regime Indicator  I = P_max - D_max', fontsize=10)

    ax = axes[2]
    ax.plot(t_axis, D_series, color='tomato',   lw=1.3, label='D_max (strain)')
    ax.plot(t_axis, P_series, color='seagreen', lw=1.3,
            label='P_max (spare capacity)')
    ax.axvline(T_DISRUPTION, color='orange', lw=1.0, ls=':')
    ax.set_ylabel('Normalised magnitude')
    ax.legend(fontsize=8, loc='upper left')
    ax.set_title('Relational Components', fontsize=10)

    ax = axes[3]
    ax.fill_between(t_axis, -1, 1, where=(I_series >= 0),
                    alpha=0.25, color='green',  label='Stable  (I > 0)')
    ax.fill_between(t_axis, -1, 1, where=(I_series < 0),
                    alpha=0.25, color='crimson', label='Divergent (I < 0)')
    ax.plot(t_axis, np.zeros(T), color='black', lw=0.8, ls='--')
    ax.axvline(T_DISRUPTION, color='orange', lw=1.0, ls=':',
               label=f'Disruption t={T_DISRUPTION}')
    if instability_t is not None:
        ax.axvline(instability_t, color='darkorchid', lw=1.0, ls=':',
                   label=f'Warning t={instability_t}')
    if failure_t is not None:
        ax.axvline(failure_t, color='crimson', lw=1.0, ls=':',
                   label=f'Failure t={failure_t}')
    if lead_time is not None:
        mid = instability_t + lead_time // 2
        ax.annotate(
            f'{lead_time} step lead',
            xy=(failure_t, 0), xytext=(mid, 0.6),
            arrowprops=dict(arrowstyle='->', color='black', lw=0.8),
            fontsize=8, ha='center'
        )
    ax.set_ylim(-1.2, 1.2)
    ax.set_ylabel('Regime zone')
    ax.set_xlabel('Time step')
    ax.legend(fontsize=8, loc='upper left')
    ax.set_title('Regime Classification', fontsize=10)

    plt.tight_layout()
    out = os.path.join(RESULTS_DIR, 'regime_early_warning.png')
    plt.savefig(out, dpi=150)
    print(f"Plot saved to: {out}")


if __name__ == '__main__':
    main()