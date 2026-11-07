"""
Experiment 02: Actuator Saturation and Anti-Windup Clamping.

Demonstrates:
1. Physical actuator force limits: -30 N <= u(t) <= +30 N.
2. Naive integration (Anti-Windup = False):
   - When the actuator saturates, the integrator continues accumulating error.
   - Result: Huge overshoot and sluggish recovery as the accumulated charge unwinds.
3. Anti-Windup Clamping (Anti-Windup = True):
   - Conditional integration halts accumulator growth when the output is saturated.
   - Result: Clean, overshoot-free response with instant recovery.

Output Plot:
    plots/02_integral_windup.png
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Ensure root directory is on sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.plant import MassSpringDamper
from src.controller import PIDController
from src.metrics import calculate_performance_metrics


def run_windup_simulation(anti_windup: bool, t_end: float = 6.0, dt: float = 0.005):
    """Run closed-loop simulation with or without anti-windup clamping."""
    plant = MassSpringDamper(mass=1.0, damping=10.0, stiffness=20.0)
    # Gains chosen to demonstrate saturation and windup
    controller = PIDController(
        kp=100.0,
        ki=120.0,
        kd=5.0,
        output_limits=(-30.0, 30.0),
        anti_windup=anti_windup,
        derivative_on_measurement=True,
    )

    n_steps = int(np.round(t_end / dt)) + 1
    t = np.linspace(0.0, t_end, n_steps)
    x = np.zeros(n_steps)
    u = np.zeros(n_steps)
    i_term = np.zeros(n_steps)
    saturated = np.zeros(n_steps, dtype=bool)

    target = 1.0

    for idx in range(1, n_steps):
        y_meas = plant.position
        u_force = controller.update(setpoint=target, measurement=y_meas, dt=dt)
        plant.step(force=u_force, dt=dt, method="rk4")

        x[idx] = plant.position
        u[idx] = u_force
        i_term[idx] = controller.integral
        saturated[idx] = controller.is_saturated

    u[0] = u[1]
    i_term[0] = i_term[1]

    return t, x, u, i_term, saturated


def main():
    print("=" * 80)
    print("EXPERIMENT 02: ACTUATOR SATURATION & INTEGRAL WINDUP EVALUATION")
    print("=" * 80)

    # 1. Run Simulations
    t, x_naive, u_naive, i_naive, sat_naive = run_windup_simulation(anti_windup=False)
    _, x_clamped, u_clamped, i_clamped, sat_clamped = run_windup_simulation(anti_windup=True)

    # 2. Compute Performance Metrics
    metrics_naive = calculate_performance_metrics(t, x_naive, target=1.0)
    metrics_clamped = calculate_performance_metrics(t, x_clamped, target=1.0)

    print(f"\n{'Metric':<28} | {'Naive (No Anti-Windup)':<24} | {'Anti-Windup Clamping':<24}")
    print("-" * 80)
    print(f"{'Peak Position (m)':<28} | {np.max(x_naive):<24.4f} | {np.max(x_clamped):<24.4f}")
    print(f"{'Percentage Overshoot (%)':<28} | {metrics_naive['overshoot_pct']:<24.2f}% | {metrics_clamped['overshoot_pct']:<24.2f}%")
    ts_naive_str = f"{metrics_naive['settling_time_s']:.3f} s" if metrics_naive['settling_time_s'] else "N/A"
    ts_clamped_str = f"{metrics_clamped['settling_time_s']:.3f} s" if metrics_clamped['settling_time_s'] else "N/A"
    print(f"{'Settling Time (2% band)':<28} | {ts_naive_str:<24} | {ts_clamped_str:<24}")
    print(f"{'Max Integral Value (N)':<28} | {np.max(i_naive):<24.2f} | {np.max(i_clamped):<24.2f}")
    print(f"{'Steady-State Error (m)':<28} | {metrics_naive['steady_state_error_m']:<24.4f} | {metrics_clamped['steady_state_error_m']:<24.4f}")
    print("-" * 80)

    # 3. Create High-Quality 3-Panel Plot
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 9), dpi=150, sharex=True)

    # Panel 1: Position
    ax1.plot(t, x_naive, label="Naive Integration (No Anti-Windup)", color="#d62728", linewidth=2.0)
    ax1.plot(t, x_clamped, label="Anti-Windup Clamping (Protected)", color="#2ca02c", linewidth=2.0)
    ax1.axhline(1.0, color="black", linestyle="--", label="Target ($x_{ref}=1.0\\,$m)")
    ax1.axhline(1.02, color="gray", linestyle=":", alpha=0.7, label="±2% Tolerance Band")
    ax1.axhline(0.98, color="gray", linestyle=":", alpha=0.7)
    ax1.set_ylabel("Position $x(t)$ (m)", fontsize=11)
    ax1.set_ylim([0.0, 1.25])
    ax1.set_title("Integral Windup Demonstration (Actuator Force Limit = ±30 N)", fontsize=12, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="lower right", framealpha=0.9)

    # Panel 2: Actuator Force u(t)
    ax2.plot(t, u_naive, color="#d62728", linewidth=1.8, label="Naive $u(t)$")
    ax2.plot(t, u_clamped, color="#2ca02c", linewidth=1.8, label="Anti-Windup $u(t)$")
    ax2.axhline(30.0, color="crimson", linestyle="--", linewidth=1.2, label="Actuator Limits ($\\pm 30\\,$N)")
    ax2.axhline(-30.0, color="crimson", linestyle="--", linewidth=1.2)
    ax2.axhline(20.0, color="black", linestyle=":", linewidth=1.2, label="Equilibrium Force ($20\\,$N)")
    ax2.set_ylabel("Force $u(t)$ (N)", fontsize=11)
    ax2.set_ylim([-35.0, 35.0])
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper right", framealpha=0.9)

    # Panel 3: Integral Term Accumulator
    ax3.plot(t, i_naive, color="#d62728", linewidth=1.8, label="Naive Integral $I(t)$")
    ax3.plot(t, i_clamped, color="#2ca02c", linewidth=1.8, label="Clamped Integral $I(t)$")
    ax3.axhline(20.0, color="black", linestyle=":", linewidth=1.2, label="Required Steady-State Integral ($20\\,$N)")
    ax3.set_xlabel("Time (s)", fontsize=11)
    ax3.set_ylabel("Integral Term $I(t)$ (N)", fontsize=11)
    ax3.set_xlim([0.0, t[-1]])
    ax3.set_ylim([0.0, 40.0])
    ax3.grid(True, linestyle=":", alpha=0.6)
    ax3.legend(loc="lower right", framealpha=0.9)

    plt.tight_layout()

    plots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plots"))
    plot_path = os.path.join(plots_dir, "02_integral_windup.png")
    plt.savefig(plot_path, dpi=200)
    plt.close()

    print(f"\nPlot successfully saved to: {plot_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
