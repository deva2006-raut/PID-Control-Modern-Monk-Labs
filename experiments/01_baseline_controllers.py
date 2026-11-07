"""
Experiment 01: Baseline Controller Comparison (P, PI, PD, and Full PID).

This script performs:
1. P-only Gain Sweep (Kp = 20, 50, 100, 200 N/m):
   - Verifies analytical steady-state formula: x_ss = Kp / (Kp + k) against simulation.
2. I-Gain Sweep (Ki = 0, 25, 50, 100 N/(m*s)):
   - Demonstrates how integral accumulation eliminates steady-state droop.
3. D-Gain Sweep (Kd = 0, 5, 15, 30 N*s/m):
   - Demonstrates artificial damping and transient stabilization.
4. Combined 4-Controller Benchmark (P vs PI vs PD vs Full PID):
   - Computes: Rise Time (tr), Overshoot (Mp), Settling Time (ts), Steady-State Error (ess).
   - Generates two-panel publication plot: Position x(t) and Actuator Force u(t).

Saved Plots:
    - plots/01_p_gain_sweep.png
    - plots/01_i_gain_sweep.png
    - plots/01_d_gain_sweep.png
    - plots/01_baseline_comparison.png
"""

import os
import sys
from typing import Tuple, Dict, Any, List
import numpy as np
import matplotlib.pyplot as plt

# Ensure root directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.plant import MassSpringDamper
from src.controller import PIDController
from src.metrics import calculate_performance_metrics


def run_closed_loop_simulation(
    kp: float,
    ki: float,
    kd: float,
    target: float = 1.0,
    t_end: float = 6.0,
    dt: float = 0.005,
    anti_windup: bool = True,
    derivative_on_measurement: bool = True,
    filter_tau: float = 0.0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Simulate closed-loop feedback control of the mass-spring-damper system.

    Returns
    -------
    time : np.ndarray
    position : np.ndarray
    control_force : np.ndarray
    """
    plant = MassSpringDamper(mass=1.0, damping=10.0, stiffness=20.0)
    controller = PIDController(
        kp=kp,
        ki=ki,
        kd=kd,
        output_limits=(-30.0, 30.0),
        filter_tau=filter_tau,
        derivative_on_measurement=derivative_on_measurement,
        anti_windup=anti_windup,
    )

    n_steps = int(np.round(t_end / dt)) + 1
    t = np.linspace(0.0, t_end, n_steps)
    x = np.zeros(n_steps)
    u = np.zeros(n_steps)

    x[0] = plant.position

    for i in range(1, n_steps):
        # Current measured feedback from plant
        y_meas = plant.position

        # Compute control force from controller
        u_force = controller.update(setpoint=target, measurement=y_meas, dt=dt)

        # Advance plant physics
        plant.step(force=u_force, dt=dt, method="rk4")

        x[i] = plant.position
        u[i] = u_force

    # Control force at t=0 taken from first calculated step
    u[0] = u[1]

    return t, x, u


def main():
    print("=" * 80)
    print("EXPERIMENT 01: BASELINE CONTROLLER COMPARISON & METRICS EVALUATION")
    print("=" * 80)

    plots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plots"))
    os.makedirs(plots_dir, exist_ok=True)

    dt = 0.005
    t_end = 6.0
    target = 1.0

    # -------------------------------------------------------------------------
    # PART 1: P-ONLY GAIN SWEEP & ANALYTICAL VERIFICATION
    # -------------------------------------------------------------------------
    kp_values = [20.0, 50.0, 100.0, 200.0]
    p_sweep_results = []

    plt.figure(figsize=(9, 5.5), dpi=150)
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

    print("\n--- PART 1: P-ONLY CONTROLLER STEADY-STATE VERIFICATION ---")
    print(f"{'Kp (N/m)':<10} | {'x_analytical (m)':<18} | {'x_simulated (m)':<18} | {'Error e_ss (m)':<16} | {'Discrepancy (m)':<16}")
    print("-" * 88)

    for kp, c in zip(kp_values, colors):
        t, x, u = run_closed_loop_simulation(kp=kp, ki=0.0, kd=0.0, target=target, t_end=t_end, dt=dt)
        x_analytical = kp / (kp + 20.0)  # x_ss = Kp / (Kp + k)
        x_sim = x[-1]
        e_ss = abs(target - x_sim)
        discrepancy = abs(x_analytical - x_sim)

        p_sweep_results.append({
            "kp": kp,
            "analytical": x_analytical,
            "simulated": x_sim,
            "ess": e_ss,
            "discrepancy": discrepancy
        })

        print(f"{kp:<10.1f} | {x_analytical:<18.4f} | {x_sim:<18.4f} | {e_ss:<16.4f} | {discrepancy:<16.6f}")

        plt.plot(t, x, label=f"$K_p={kp:.0f}\\,$N/m ($x_{{ss}}={x_analytical:.3f}\\,$m)", color=c, linewidth=2.0)
        plt.axhline(x_analytical, color=c, linestyle=":", alpha=0.6)

    plt.axhline(target, color="black", linestyle="--", linewidth=1.5, label="Target ($x_{ref}=1.0\\,$m)")
    plt.title("Proportional-Only Control: Effect of Gain $K_p$ on Steady-State Droop", fontsize=12, fontweight="bold")
    plt.xlabel("Time (s)", fontsize=11)
    plt.ylabel("Position $x(t)$ (m)", fontsize=11)
    plt.xlim([0.0, t_end])
    plt.ylim([0.0, 1.1])
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="lower right", framealpha=0.9)
    plt.tight_layout()
    p_sweep_plot = os.path.join(plots_dir, "01_p_gain_sweep.png")
    plt.savefig(p_sweep_plot, dpi=200)
    plt.close()
    print(f"-> Saved: {p_sweep_plot}")

    # -------------------------------------------------------------------------
    # PART 2: I-GAIN SWEEP (ELIMINATION OF STEADY-STATE ERROR)
    # -------------------------------------------------------------------------
    print("\n--- PART 2: INTEGRAL GAIN SWEEP (FIXED Kp = 100, Kd = 0) ---")
    ki_values = [0.0, 25.0, 50.0, 100.0]
    plt.figure(figsize=(9, 5.5), dpi=150)

    for ki, c in zip(ki_values, colors):
        t, x, u = run_closed_loop_simulation(kp=100.0, ki=ki, kd=0.0, target=target, t_end=t_end, dt=dt)
        lbl = f"$K_i={ki:.0f}\\,$N/(m·s) (Final: {x[-1]:.3f} m)"
        plt.plot(t, x, label=lbl, color=c, linewidth=2.0)

    plt.axhline(target, color="black", linestyle="--", linewidth=1.5, label="Target ($x_{ref}=1.0\\,$m)")
    plt.axhline(target * 0.98, color="gray", linestyle=":", alpha=0.7, label="±2% Settling Band")
    plt.axhline(target * 1.02, color="gray", linestyle=":", alpha=0.7)
    plt.title("Integral Action: Eliminating Steady-State Error ($K_p=100$, $K_d=0$)", fontsize=12, fontweight="bold")
    plt.xlabel("Time (s)", fontsize=11)
    plt.ylabel("Position $x(t)$ (m)", fontsize=11)
    plt.xlim([0.0, t_end])
    plt.ylim([0.0, 1.1])
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="lower right", framealpha=0.9)
    plt.tight_layout()
    i_sweep_plot = os.path.join(plots_dir, "01_i_gain_sweep.png")
    plt.savefig(i_sweep_plot, dpi=200)
    plt.close()
    print(f"-> Saved: {i_sweep_plot}")

    # -------------------------------------------------------------------------
    # PART 3: D-GAIN SWEEP (DAMPING & OVERSHOOT SUPPRESSION)
    # -------------------------------------------------------------------------
    print("\n--- PART 3: DERIVATIVE GAIN SWEEP (FIXED Kp = 100, Ki = 80) ---")
    kd_values = [0.0, 5.0, 15.0, 30.0]
    plt.figure(figsize=(9, 5.5), dpi=150)

    for kd, c in zip(kd_values, colors):
        t, x, u = run_closed_loop_simulation(kp=100.0, ki=80.0, kd=kd, target=target, t_end=t_end, dt=dt)
        metrics = calculate_performance_metrics(t, x, target=target)
        lbl = f"$K_d={kd:.0f}\\,$N·s/m ($M_p={metrics['overshoot_pct']:.1f}\\%$, $t_s={metrics['settling_time_s']:.2f}\\,$s)"
        plt.plot(t, x, label=lbl, color=c, linewidth=2.0)

    plt.axhline(target, color="black", linestyle="--", linewidth=1.5, label="Target ($x_{ref}=1.0\\,$m)")
    plt.axhline(target * 0.98, color="gray", linestyle=":", alpha=0.7, label="±2% Settling Band")
    plt.axhline(target * 1.02, color="gray", linestyle=":", alpha=0.7)
    plt.title("Derivative Action: Damping and Transient Shaping ($K_p=100$, $K_i=80$)", fontsize=12, fontweight="bold")
    plt.xlabel("Time (s)", fontsize=11)
    plt.ylabel("Position $x(t)$ (m)", fontsize=11)
    plt.xlim([0.0, t_end])
    plt.ylim([0.0, 1.1])
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="lower right", framealpha=0.9)
    plt.tight_layout()
    d_sweep_plot = os.path.join(plots_dir, "01_d_gain_sweep.png")
    plt.savefig(d_sweep_plot, dpi=200)
    plt.close()
    print(f"-> Saved: {d_sweep_plot}")

    # -------------------------------------------------------------------------
    # PART 4: COMBINED 4-CONTROLLER BENCHMARK COMPARISON
    # -------------------------------------------------------------------------
    print("\n--- PART 4: COMPREHENSIVE 4-CONTROLLER BENCHMARK ---")

    controllers = {
        "P Controller":   {"kp": 100.0, "ki": 0.0,  "kd": 0.0,  "color": "#1f77b4", "linestyle": "-"},
        "PI Controller":  {"kp": 100.0, "ki": 80.0, "kd": 0.0,  "color": "#ff7f0e", "linestyle": "--"},
        "PD Controller":  {"kp": 100.0, "ki": 0.0,  "kd": 15.0, "color": "#2ca02c", "linestyle": "-."},
        "PID Controller": {"kp": 100.0, "ki": 80.0, "kd": 15.0, "color": "#d62728", "linestyle": "-"},
    }

    fig, (ax_pos, ax_force) = plt.subplots(2, 1, figsize=(11, 8.5), dpi=150, sharex=True)

    benchmark_table: List[Dict[str, Any]] = []

    for name, cfg in controllers.items():
        t, x, u = run_closed_loop_simulation(
            kp=cfg["kp"], ki=cfg["ki"], kd=cfg["kd"],
            target=target, t_end=t_end, dt=dt
        )
        metrics = calculate_performance_metrics(t, x, target=target)

        benchmark_table.append({
            "Controller": name,
            "Gains (Kp, Ki, Kd)": f"({cfg['kp']:.0f}, {cfg['ki']:.0f}, {cfg['kd']:.0f})",
            "Rise Time tr (s)": f"{metrics['rise_time_s']:.3f}" if metrics['rise_time_s'] is not None else "N/A*",
            "Overshoot Mp (%)": f"{metrics['overshoot_pct']:.2f}%",
            "Settling Time ts (s)": f"{metrics['settling_time_s']:.3f}" if metrics['settling_time_s'] is not None else "N/A**",
            "Steady-State Error ess (m)": f"{metrics['steady_state_error_m']:.4f}",
            "Final Position (m)": f"{metrics['final_value_m']:.4f}",
        })

        # Plot Position
        ax_pos.plot(t, x, label=f"{name} ({cfg['kp']:.0f}, {cfg['ki']:.0f}, {cfg['kd']:.0f})",
                    color=cfg["color"], linestyle=cfg["linestyle"], linewidth=2.0)

        # Plot Control Force
        ax_force.plot(t, u, label=f"{name}", color=cfg["color"], linestyle=cfg["linestyle"], linewidth=1.8)

    # Position Subplot Decorators
    ax_pos.axhline(target, color="black", linestyle="--", linewidth=1.5, label="Target ($x_{ref}=1.0\\,$m)")
    ax_pos.axhline(target * 0.98, color="gray", linestyle=":", alpha=0.7, label="±2% Tolerance Band")
    ax_pos.axhline(target * 1.02, color="gray", linestyle=":", alpha=0.7)
    ax_pos.set_title("Step Response Comparison: P vs. PI vs. PD vs. Full PID", fontsize=12, fontweight="bold")
    ax_pos.set_ylabel("Position $x(t)$ (m)", fontsize=11)
    ax_pos.set_ylim([-0.05, 1.15])
    ax_pos.grid(True, linestyle=":", alpha=0.6)
    ax_pos.legend(loc="lower right", framealpha=0.9, fontsize=9.5)

    # Control Force Subplot Decorators
    ax_force.axhline(30.0, color="crimson", linestyle="--", linewidth=1.2, label="Actuator Limits ($\\pm 30\\,$N)")
    ax_force.axhline(-30.0, color="crimson", linestyle="--", linewidth=1.2)
    ax_force.axhline(20.0, color="black", linestyle=":", linewidth=1.2, label="Equilibrium Force ($u_{ss}=20\\,$N)")
    ax_force.set_title("Actuator Control Force $u(t)$ with Saturation Limits", fontsize=12, fontweight="bold")
    ax_force.set_xlabel("Time (s)", fontsize=11)
    ax_force.set_ylabel("Force $u(t)$ (N)", fontsize=11)
    ax_force.set_xlim([0.0, t_end])
    ax_force.set_ylim([-35.0, 35.0])
    ax_force.grid(True, linestyle=":", alpha=0.6)
    ax_force.legend(loc="upper right", framealpha=0.9, fontsize=9.5)

    plt.tight_layout()
    baseline_comparison_plot = os.path.join(plots_dir, "01_baseline_comparison.png")
    plt.savefig(baseline_comparison_plot, dpi=200)
    plt.close()
    print(f"-> Saved: {baseline_comparison_plot}")

    # Print Table
    print("\n" + "=" * 105)
    print(f"{'Controller':<16} | {'Gains (Kp,Ki,Kd)':<18} | {'Rise Time (s)':<14} | {'Overshoot (%)':<14} | {'Settling Time (s)':<18} | {'SSE (m)':<10}")
    print("=" * 105)
    for row in benchmark_table:
        print(f"{row['Controller']:<16} | {row['Gains (Kp, Ki, Kd)']:<18} | {row['Rise Time tr (s)']:<14} | {row['Overshoot Mp (%)']:<14} | {row['Settling Time ts (s)']:<18} | {row['Steady-State Error ess (m)']:<10}")
    print("=" * 105)
    print("*  N/A: Controller never reaches 90% of setpoint due to steady-state droop.")
    print("** N/A: Controller never enters the 2% tolerance band [0.98 m, 1.02 m].")
    print("=" * 105)


if __name__ == "__main__":
    main()
