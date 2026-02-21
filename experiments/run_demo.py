import sys
import os
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sc_sim.network     import build_network
from sc_sim.flow        import simulate
from sc_sim.disruption  import capacity_drop
from sc_sim.instability import rolling_variance, kendall_tau_trend
from sc_sim.metrics     import compute_trigger_times

T                = 300
DISRUPTION_TIME  = 150
DISRUPTION_NODE  = 'W1'
NEW_CAPACITY     = 20.0
BACKLOG_THRESHOLD = 200.0
TAU_THRESHOLD    = 0.60
ROLLING_WINDOW   = 20
TAU_WINDOW       = 30


def main():
    G          = build_network()
    disruption = capacity_drop(DISRUPTION_NODE, NEW_CAPACITY, DISRUPTION_TIME)
    backlog    = simulate(G, T=T, disruption_fn=disruption)

    rv  = rolling_variance(backlog, window=ROLLING_WINDOW)
    tau = kendall_tau_trend(rv, window=TAU_WINDOW)

    instability_t, failure_t, lead_time = compute_trigger_times(
        backlog, tau,
        tau_threshold=TAU_THRESHOLD,
        backlog_threshold=BACKLOG_THRESHOLD,
    )

    tau_val = tau[instability_t] if instability_t is not None else float('nan')
    print(f"Kendall tau at detection:   {tau_val:.4f}")
    print(f"Instability detected:       t = {instability_t}")
    print(f"Failure threshold crossed:  t = {failure_t}")
    print(f"Lead time:                  {lead_time} steps")

    t_axis = np.arange(T)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)

    ax1.plot(t_axis, backlog, color='steelblue', lw=1.5, label='Total backlog')
    ax1.axvline(DISRUPTION_TIME, color='crimson',    ls='--', alpha=0.7,
                label=f'Disruption (t={DISRUPTION_TIME})')
    if instability_t is not None:
        ax1.axvline(instability_t, color='forestgreen', ls=':', lw=2,
                    label=f'Instability detected (t={instability_t})')
    if failure_t is not None:
        ax1.axvline(failure_t, color='darkorange', ls=':', lw=2,
                    label=f'Failure threshold (t={failure_t})')
    ax1.axhline(BACKLOG_THRESHOLD, color='darkorange', ls='--', alpha=0.3)
    ax1.set_ylabel('Total Network Backlog')
    ax1.set_title('Supply Chain Early Warning — Cascade Detection')
    ax1.legend(fontsize=8)

    ax2.plot(t_axis, rv, color='darkorange', lw=1.5,
             label=f'Rolling variance (w={ROLLING_WINDOW})')
    if instability_t is not None:
        ax2.axvline(instability_t, color='forestgreen', ls=':', lw=2)
    ax2.set_ylabel('Rolling Variance of Backlog')
    ax2.set_xlabel('Time Step')
    ax2.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig('supply_chain_early_warning.png', dpi=120)
    plt.show()
    print("Plot saved -> supply_chain_early_warning.png")


if __name__ == '__main__':
    main()
