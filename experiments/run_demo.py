"""
run_demo.py — Supply Chain Early Warning Demo

Demonstrates relational regime detection on a minimal 3-4-5
supply network. At t=150, warehouse W1 suffers a severe capacity
drop. The regime indicator I = P_max - D_max crosses zero before
backlog reaches the failure threshold, providing structural
early warning without statistical inference or tuning parameters.

Usage
-----
    python experiments/run_demo.py

Output
------
    Console report of trigger times and lead time.
    Four-panel plot saved to results/regime_early_warning.png
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

# ----------------------------------------------------------------
# Parameters
# ----------------------------------------------------------------
T                  = 300
DISRUPTION_TIME    = 150
DISRUPTION_NODE    = 'W1'
DISRUPTION_CAP     = 20.0
BACKLOG_THRESHOLD  = 200.0
RESULTS_DIR        = os.path.join(os.path.dirname(__file__), '..', 'results')

os.makedirs(RESULTS_DIR, exist_ok=True)

# ----------------------------------------------------------------
# Build network and disruption
# ----------------------------------------------------------------
G   = build_network()
dfn = capacity_drop(DISRUPTION_NODE, DISRUPTION_CAP, DISRUPTION_TIME)

# ----------------------------------------------------------------
# Run simulation
# simulate() returns (backlog, G_states)
# G_states is a list of (G_snapshot, pipelines_snapshot) per step
# ----------------------------------------------------------------
backlog, G_states = simulate(G, T=T, disruption_fn=dfn)

# ----------------------------------------------------------------
# Compute regime indicator series from recorded states
# ----------------------------------------------------------------
I_series, D_series, P_series = regime_series(G_states)

# ----------------------------------------------------------------
# Identify trigger times
# ----------------------------------------------------------------
instability_time, failure_time, lead_time = compute_trigger_times(
    backlog, I_series, backlog_threshold=BACKLOG_THRESHOLD
)

# ----------------------------------------------------------------
# Console report
# ----------------------------------------------------------------
print()
print("=" * 52)
print("  Supply Chain Early Warning — Regime Indicator")
print("=" * 52)
print(f"  Disruption applied :  t = {DISRUPTION_TIME}")

if instability_time is not None:
    print(f"  Regime I < 0 at    :  t = {instability_time}  (divergent)")
else:
    print("  Regime I < 0       :  not reached")

if failure_time is not None:
    print(f"  Backlog threshold  :  t = {failure_time}  "
          f"(backlog >= {BACKLOG_THRESHOLD})")
else:
    print("  Backlog threshold  :  not reached")

if lead_time is not None:
    print(f"  Lead time          :  {lead_time} steps before failure")
else:
    print("  Lead time          :  N/A")

print("=" * 52)
print()

# ----------------------------------------------------------------
# Plot — four panels
#
# Panel 1: Total backlog with failure threshold
# Panel 2: Regime indicator I with zero crossing marked
# Panel 3: D_max (relational strain) and P_max (spare capacity)
# Panel 4: Regime zone — coloured bands for stable / critical /
#          divergent regions to make the mathematics visible
# ----------------------------------------------------------------
t = np.arange(T)
fig, axes = plt.subplots(4, 1, figsize=(11, 13), sharex=True)
fig.suptitle(
    'Supply Chain Early Warning — Relational Regime Indicator\n'
    r'$I = P_{\max} - D_{\max}$   '
    r'$I > 0$ stable   $I = 0$ critical   $I < 0$ divergent',
    fontsize=12
)

# -- Panel 1: Backlog
ax = axes[0]
ax.plot(t, backlog, color='steelblue', lw=1.5, label='Total backlog')
ax.axhline(BACKLOG_THRESHOLD, color='crimson', lw=1.2,
           ls='--', label=f'Failure threshold ({BACKLOG_THRESHOLD})')
ax.axvline(DISRUPTION_TIME, color='orange', lw=1.0,
           ls=':', label=f'Disruption t={DISRUPTION_TIME}')
if failure_time is not None:
    ax.axvline(failure_time, color='crimson', lw=1.0,
               ls=':', label=f'Failure t={failure_time}')
ax.set_ylabel('Backlog (units)')
ax.legend(fontsize=8, loc='upper left')
ax.set_title('Total System Backlog', fontsize=10)

# -- Panel 2: Regime indicator I
ax = axes[1]
ax.plot(t, I_series, color='darkorchid', lw=1.5, label='I = P_max − D_max')
ax.axhline(0.0, color='black', lw=0.8, ls='--', label='Critical boundary (I = 0)')
ax.axvline(DISRUPTION_TIME, color='orange', lw=1.0, ls=':')
if instability_time is not None:
    ax.axvline(instability_time, color='darkorchid', lw=1.0,
               ls=':', label=f'I < 0 at t={instability_time}')
if failure_time is not None:
    ax.axvline(failure_time, color='crimson', lw=1.0, ls=':')
ax.fill_between(t, I_series, 0,
                where=(I_series < 0),
                alpha=0.15, color='crimson', label='Divergent region')
ax.fill_between(t, I_series, 0,
                where=(I_series >= 0),
                alpha=0.10, color='green', label='Stable region')
ax.set_ylabel('I (regime indicator)')
ax.legend(fontsize=8, loc='upper left')
ax.set_title('Regime Indicator  I = P_max − D_max', fontsize=10)

# -- Panel 3: D_max and P_max
ax = axes[2]
ax.plot(t, D_max := D_series, color='tomato',    lw=1.3, label='D_max (strain)')
ax.plot(t, P_max := P_series, color='seagreen',  lw=1.3, label='P_max (spare capacity)')
ax.axvline(DISRUPTION_TIME, color='orange', lw=1.0, ls=':')
ax.set_ylabel('Normalised magnitude')
ax.legend(fontsize=8, loc='upper left')
ax.set_title('Relational Components', fontsize=10)

# -- Panel 4: Regime zone
ax = axes[3]
regime = np.sign(I_series)
colors = np.where(I_series > 0, 0.7, np.where(I_series == 0, 0.5, 0.2))
ax.fill_between(t, -1, 1,
                where=(I_series >= 0),
                alpha=0.25, color='green',  label='Stable  (I > 0)')
ax.fill_between(t, -1, 1,
                where=(I_series < 0),
                alpha=0.25, color='crimson', label='Divergent (I < 0)')
ax.plot(t, np.zeros(T), color='black', lw=0.8, ls='--')
ax.axvline(DISRUPTION_TIME, color='orange', lw=1.0, ls=':',
           label=f'Disruption t={DISRUPTION_TIME}')
if instability_time is not None:
    ax.axvline(instability_time, color='darkorchid', lw=1.0, ls=':',
               label=f'Warning  t={instability_time}')
if failure_time is not None:
    ax.axvline(failure_time, color='crimson', lw=1.0, ls=':',
               label=f'Failure  t={failure_time}')
if lead_time is not None:
    mid = instability_time + lead_time // 2
    ax.annotate(
        f'{lead_time} step lead',
        xy=(failure_time, 0), xytext=(mid, 0.6),
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
