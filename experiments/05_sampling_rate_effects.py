"""
Experiment 05: Discrete-Time Sampling Rate and Discretization Effects.

Demonstrates:
1. Microcontroller Discretization & Zero-Order Hold (ZOH):
   - Real digital controllers (e.g. STM32, Arduino, DSPs) sample at discrete intervals Ts = 1 / f_s.
   - The computed actuator force u is held constant between samples (Zero-Order Hold).
2. Sampling Frequencies Analyzed:
   - 200 Hz (Ts = 5 ms) : Fast baseline (near-continuous performance).
   - 50 Hz  (Ts = 20 ms): Typical industrial loop rate.
   - 20 Hz  (Ts = 50 ms): Moderate delay.
   - 10 Hz  (Ts = 100 ms): Noticeable degradation in smoothness.
   - 5 Hz   (Ts = 200 ms): Strong phase lag, transient overshoot; poorly damped / does not settle within simulation window.
   - 2 Hz   (Ts = 500 ms): Severe phase lag (ZOH delay approx Ts/2); poorly damped / does not settle within simulation window.

Output Plot:
    plots/05_sampling_rate_effects.png
"""

import os
import sys
from typing import Dict, Any, List
import numpy as np
import matplotlib.pyplot as plt

# Ensure root directory is on sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.plant import MassSpringDamper
from src.controller import PIDController
from src.metrics import calculate_performance_metrics


def run_sampled_simulation(
    sampling_freq_hz: float,
    t_end: float = 6.0,
    dt_sim: float = 0.001,
):
    """
    Simulate continuous physical plant driven by a discrete sampled controller with ZOH.

    Parameters
    ----------
    sampling_freq_hz : float
        Controller execution frequency in Hertz [Hz].
    t_end : float
        Simulation duration [s].
    dt_sim : float
        Fine physics integration step [s].
    """
    plant = MassSpringDamper(mass=1.0, damping=10.0, stiffness=20.0)
    controller = PIDController(
        kp=100.0,
        ki=80.0,
        kd=15.0,
        output_limits=(-30.0, 30.0),
        derivative_on_measurement=True,
        anti_windup=True,
    )

    dt_ctrl = 1.0 / sampling_freq_hz
    n_sim_steps = int(np.round(t_end / dt_sim)) + 1
    t = np.linspace(0.0, t_end, n_sim_steps)
    x = np.zeros(n_sim_steps)
    u_held = np.zeros(n_sim_steps)

    current_u = 0.0
    time_since_last_ctrl = dt_ctrl  # Trigger update at t=0

    for i in range(n_sim_steps):
        time_since_last_ctrl += dt_sim

        # Discrete controller execution trigger
        if time_since_last_ctrl >= (dt_ctrl - 1e-9):
            # Controller samples position and computes next output
            current_u = controller.update(setpoint=1.0, measurement=plant.position, dt=dt_ctrl)
            time_since_last_ctrl = 0.0

        # Continuous physical plant integrates under Zero-Order Hold force
        plant.step(force=current_u, dt=dt_sim, method="rk4")

        x[i] = plant.position
        u_held[i] = current_u

    return t, x, u_held


def main():
    print("=" * 80)
    print("EXPERIMENT 05: SAMPLING RATE & DISCRETIZATION STABILITY EVALUATION")
    print("=" * 80)

    frequencies = [200.0, 50.0, 20.0, 10.0, 5.0, 2.0]
    colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd", "#e377c2", "#d62728"]

    results_table: List[Dict[str, Any]] = []

    fig, (ax_pos, ax_force) = plt.subplots(2, 1, figsize=(11, 8.5), dpi=150, sharex=True)

    print(f"\n{'Sampling Rate':<18} | {'Ts (ms)':<10} | {'Rise Time (s)':<14} | {'Overshoot (%)':<14} | {'Settling Time (s)':<18} | {'Stability Status':<16}")
    print("-" * 96)

    for freq, col in zip(frequencies, colors):
        dt_ctrl_ms = (1.0 / freq) * 1000.0
        t, x, u = run_sampled_simulation(sampling_freq_hz=freq)
        metrics = calculate_performance_metrics(t, x, target=1.0)

        # Classify stability based on settling and damping in simulation window
        last_sec_range = np.max(x[-1000:]) - np.min(x[-1000:])
        if last_sec_range > 0.05:
            status = "Poorly damped / does not settle within simulation window"
        else:
            status = "STABLE"

        tr_str = f"{metrics['rise_time_s']:.3f}" if metrics['rise_time_s'] else "N/A"
        ts_str = f"{metrics['settling_time_s']:.3f}" if metrics['settling_time_s'] else "N/A"

        results_table.append({
            "freq": freq,
            "ts_ms": dt_ctrl_ms,
            "tr": tr_str,
            "mp": metrics['overshoot_pct'],
            "ts": ts_str,
            "status": status,
        })

        print(f"{freq:<5.0f} Hz ({dt_ctrl_ms:>4.0f} ms) | {dt_ctrl_ms:<10.1f} | {tr_str:<14} | {metrics['overshoot_pct']:<14.2f}% | {ts_str:<18} | {status}")

        # Plot curves
        ax_pos.plot(t, x, label=f"{freq:.0f} Hz ($T_s={dt_ctrl_ms:.0f}\\,$ms) - {status}", color=col, linewidth=1.8 if freq != 200 else 2.2)
        ax_force.plot(t, u, label=f"{freq:.0f} Hz", color=col, linewidth=1.5 if freq != 200 else 2.0)

    # Decorate Position Plot
    ax_pos.axhline(1.0, color="black", linestyle="--", linewidth=1.5, label="Target ($x_{ref}=1.0\\,$m)")
    ax_pos.axhline(1.02, color="gray", linestyle=":", alpha=0.7, label="$\\pm 2\\%$ Tolerance Band")
    ax_pos.axhline(0.98, color="gray", linestyle=":", alpha=0.7)
    ax_pos.set_title("Effect of Controller Sampling Rate ($f_s = 2\\,$Hz to $200\\,$Hz) with Zero-Order Hold", fontsize=12, fontweight="bold")
    ax_pos.set_ylabel("Position $x(t)$ (m)", fontsize=11)
    ax_pos.set_ylim([-0.4, 1.4])
    ax_pos.grid(True, linestyle=":", alpha=0.6)
    ax_pos.legend(loc="lower right", framealpha=0.9, fontsize=9.0)

    # Decorate Force Plot
    ax_force.axhline(30.0, color="crimson", linestyle="--", linewidth=1.2, label="Actuator Limits ($\\pm 30\\,$N)")
    ax_force.axhline(-30.0, color="crimson", linestyle="--", linewidth=1.2)
    ax_force.axhline(20.0, color="black", linestyle=":", linewidth=1.2, label="Equilibrium Force ($20\\,$N)")
    ax_force.set_title("Actuator Control Force $u(t)$ Under Zero-Order Hold Sampling", fontsize=11, fontweight="bold")
    ax_force.set_xlabel("Time (s)", fontsize=11)
    ax_force.set_ylabel("Force $u(t)$ (N)", fontsize=11)
    ax_force.set_xlim([0.0, t[-1]])
    ax_force.set_ylim([-35.0, 35.0])
    ax_force.grid(True, linestyle=":", alpha=0.6)
    ax_force.legend(loc="upper right", framealpha=0.9, fontsize=9.0)

    plt.tight_layout()

    plots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plots"))
    plot_path = os.path.join(plots_dir, "05_sampling_rate_effects.png")
    plt.savefig(plot_path, dpi=200)
    plt.close()

    print(f"\nPlot successfully saved to: {plot_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
