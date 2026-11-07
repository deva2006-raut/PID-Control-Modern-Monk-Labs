"""
Experiment 06: Heuristic Manual PID Tuning Sequence.

Demonstrates the classic practical tuning workflow used by control and robotics engineers:
1. Step 1 (Proportional Tuning):
   - Set Ki = 0, Kd = 0.
   - Gradually increase Kp to get a fast rise toward the setpoint.
   - Observe the fundamental limitation: physical spring stiffness (k = 20 N/m)
     forces steady-state droop: x_ss = Kp / (Kp + k) < 1.0 m.
2. Step 2 (Derivative Tuning):
   - Set Kp to a responsive value (Kp = 100 N/m).
   - Add Kd to introduce artificial viscous damping (braking) and suppress rate of change.
3. Step 3 (Integral Tuning):
   - Add Ki to eliminate the remaining steady-state error (e_ss -> 0).
   - If Ki is too small: sluggish convergence.
   - If Ki is well-tuned (Ki = 80): fast, zero-overshoot settling.
   - If Ki is too large (Ki = 180): causes overshoot, ringing, and actuator saturation.

Plant Parameters:
    m = 1.0 kg, c = 10.0 N*s/m, k = 20.0 N/m, target = 1.0 m, limits = +/- 30 N.

Output Plot:
    plots/06_manual_tuning.png
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


def run_simulation(kp: float, ki: float, kd: float, t_end: float = 6.0, dt: float = 0.005):
    """Run a closed-loop simulation and return t, x, u."""
    plant = MassSpringDamper(mass=1.0, damping=10.0, stiffness=20.0)
    controller = PIDController(
        kp=kp,
        ki=ki,
        kd=kd,
        output_limits=(-30.0, 30.0),
        derivative_on_measurement=True,
        anti_windup=True,
    )

    n_steps = int(np.round(t_end / dt)) + 1
    t = np.linspace(0.0, t_end, n_steps)
    x = np.zeros(n_steps)
    u = np.zeros(n_steps)

    for i in range(1, n_steps):
        u_force = controller.update(setpoint=1.0, measurement=plant.position, dt=dt)
        plant.step(force=u_force, dt=dt, method="rk4")
        x[i] = plant.position
        u[i] = u_force

    u[0] = u[1]
    return t, x, u


def main():
    print("=" * 85)
    print("EXPERIMENT 06: SYSTEMATIC HEURISTIC MANUAL PID TUNING")
    print("=" * 85)

    plots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plots"))
    os.makedirs(plots_dir, exist_ok=True)

    dt = 0.005
    t_end = 6.0
    target = 1.0

    # Define the 4 milestone configurations in the manual tuning journey
    configurations = [
        {"name": "Stage 1: P-Only (Kp=100)",             "kp": 100.0, "ki": 0.0,   "kd": 0.0,  "color": "#1f77b4", "ls": "--"},
        {"name": "Stage 2: PD Dampened (Kp=100, Kd=15)", "kp": 100.0, "ki": 0.0,   "kd": 15.0, "color": "#2ca02c", "ls": "-."},
        {"name": "Stage 3: Balanced PID (Optimal)",      "kp": 100.0, "ki": 80.0,  "kd": 15.0, "color": "#d62728", "ls": "-"},
        {"name": "Stage 4: Over-Integrated (Aggressive)","kp": 100.0, "ki": 180.0, "kd": 5.0,  "color": "#9467bd", "ls": ":"},
    ]

    fig, (ax_pos, ax_force) = plt.subplots(2, 1, figsize=(11, 8.5), dpi=150, sharex=True)
    table_data: List[Dict[str, Any]] = []

    print(f"\n{'Tuning Stage':<35} | {'Gains (Kp, Ki, Kd)':<20} | {'tr (s)':<10} | {'Mp (%)':<10} | {'ts (s)':<12} | {'ess (m)':<10}")
    print("-" * 105)

    for cfg in configurations:
        t, x, u = run_simulation(kp=cfg["kp"], ki=cfg["ki"], kd=cfg["kd"], t_end=t_end, dt=dt)
        metrics = calculate_performance_metrics(t, x, target=target)

        tr_str = f"{metrics['rise_time_s']:.3f}" if metrics['rise_time_s'] is not None else "N/A*"
        ts_str = f"{metrics['settling_time_s']:.3f}" if metrics['settling_time_s'] is not None else "N/A**"
        gains_str = f"({cfg['kp']:.0f}, {cfg['ki']:.0f}, {cfg['kd']:.0f})"

        table_data.append({
            "stage": cfg["name"],
            "gains": gains_str,
            "tr": tr_str,
            "mp": metrics['overshoot_pct'],
            "ts": ts_str,
            "ess": metrics['steady_state_error_m'],
        })

        print(f"{cfg['name']:<35} | {gains_str:<20} | {tr_str:<10} | {metrics['overshoot_pct']:<10.2f}% | {ts_str:<12} | {metrics['steady_state_error_m']:<10.4f}")

        # Plot curves
        lbl = f"{cfg['name']} {gains_str}"
        ax_pos.plot(t, x, label=lbl, color=cfg["color"], linestyle=cfg["ls"], linewidth=2.0)
        ax_force.plot(t, u, label=cfg["name"], color=cfg["color"], linestyle=cfg["ls"], linewidth=1.8)

    # Position Decorators
    ax_pos.axhline(target, color="black", linestyle="--", linewidth=1.5, label="Target ($x_{ref}=1.0\\,$m)")
    ax_pos.axhline(target * 0.98, color="gray", linestyle=":", alpha=0.7, label="±2% Tolerance Band")
    ax_pos.axhline(target * 1.02, color="gray", linestyle=":", alpha=0.7)
    ax_pos.set_title("Heuristic Manual Tuning Sequence: From P-Only to Balanced PID", fontsize=12, fontweight="bold")
    ax_pos.set_ylabel("Position $x(t)$ (m)", fontsize=11)
    ax_pos.set_ylim([0.0, 1.25])
    ax_pos.grid(True, linestyle=":", alpha=0.6)
    ax_pos.legend(loc="lower right", framealpha=0.9, fontsize=9.0)

    # Control Force Decorators
    ax_force.axhline(30.0, color="crimson", linestyle="--", linewidth=1.2, label="Actuator Limits ($\\pm 30\\,$N)")
    ax_force.axhline(-30.0, color="crimson", linestyle="--", linewidth=1.2)
    ax_force.axhline(20.0, color="black", linestyle=":", linewidth=1.2, label="Equilibrium Force ($20\\,$N)")
    ax_force.set_title("Actuator Force $u(t)$ During Manual Tuning Progression", fontsize=11, fontweight="bold")
    ax_force.set_xlabel("Time (s)", fontsize=11)
    ax_force.set_ylabel("Force $u(t)$ (N)", fontsize=11)
    ax_force.set_xlim([0.0, t_end])
    ax_force.set_ylim([-35.0, 35.0])
    ax_force.grid(True, linestyle=":", alpha=0.6)
    ax_force.legend(loc="upper right", framealpha=0.9, fontsize=9.0)

    plt.tight_layout()
    plot_path = os.path.join(plots_dir, "06_manual_tuning.png")
    plt.savefig(plot_path, dpi=200)
    plt.close()

    print("-" * 105)
    print("*  N/A: Controller never reaches 90% of setpoint due to steady-state droop.")
    print("** N/A: Controller never enters the 2% tolerance band [0.98 m, 1.02 m].")
    print(f"\nPlot saved to: {plot_path}")
    print("=" * 85)


if __name__ == "__main__":
    main()
