"""
Experiment 00: Open-Loop Plant Dynamics & Steady-State Verification.

This script tests the Mass-Spring-Damper system without any feedback controller.
It demonstrates:
1. Free response: Releasing mass from x0 = 1.0 m with zero applied force (u = 0 N).
2. Step response (10 N): Applying u = 10 N to see mass settle at x_ss = 0.5 m.
3. Step response (20 N): Applying u = 20 N to verify holding the mass at x = 1.0 m.
4. Numerical integrator comparison: Forward Euler vs. Runge-Kutta 4 (RK4).

Output plot:
    plots/00_open_loop_response.png
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Ensure root project directory is on Python path so 'src' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.plant import MassSpringDamper


def run_open_loop_simulation(
    force: float,
    t_end: float = 3.0,
    dt: float = 0.005,
    x0: float = 0.0,
    v0: float = 0.0,
    method: str = "rk4",
):
    """Run an open-loop simulation for a constant force input."""
    plant = MassSpringDamper(
        mass=1.0,
        damping=10.0,
        stiffness=20.0,
        initial_position=x0,
        initial_velocity=v0,
    )
    time_steps = int(np.round(t_end / dt)) + 1
    t = np.linspace(0.0, t_end, time_steps)
    x = np.zeros(time_steps)
    v = np.zeros(time_steps)

    x[0] = plant.position
    v[0] = plant.velocity

    for i in range(1, time_steps):
        pos, vel = plant.step(force=force, dt=dt, method=method)
        x[i] = pos
        v[i] = vel

    return t, x, v


def main():
    print("=" * 70)
    print("EXPERIMENT 00: OPEN-LOOP MASS-SPRING-DAMPER SIMULATION")
    print("=" * 70)

    # 1. Inspect System Characteristics
    sample_plant = MassSpringDamper(mass=1.0, damping=10.0, stiffness=20.0)
    omega_n = sample_plant.natural_frequency
    zeta = sample_plant.damping_ratio
    print(f"System Parameters:")
    print(f"  • Mass (m):               {sample_plant.m:.1f} kg")
    print(f"  • Damping (c):            {sample_plant.c:.1f} N*s/m")
    print(f"  • Spring stiffness (k):   {sample_plant.k:.1f} N/m")
    print(f"  • Natural Frequency (wn): {omega_n:.3f} rad/s")
    print(f"  • Damping Ratio (zeta):   {zeta:.3f} (zeta > 1 => Overdamped system)")
    print(f"  • Force to hold at 1.0m:  {sample_plant.steady_state_force(1.0):.1f} N (k * x = 20 * 1)")
    print("-" * 70)

    # 2. Simulate Scenarios
    dt = 0.005
    t_end = 2.5

    # Scenario A: Free decay from x = 1.0 m, u = 0 N
    t_free, x_free, _ = run_open_loop_simulation(force=0.0, t_end=t_end, dt=dt, x0=1.0, v0=0.0)

    # Scenario B: Step force u = 10 N, x0 = 0.0 m
    t_10N, x_10N, _ = run_open_loop_simulation(force=10.0, t_end=t_end, dt=dt, x0=0.0, v0=0.0)

    # Scenario C: Step force u = 20 N, x0 = 0.0 m
    t_20N, x_20N, _ = run_open_loop_simulation(force=20.0, t_end=t_end, dt=dt, x0=0.0, v0=0.0)

    # Scenario D: Integrator comparison with larger dt = 0.08 s (Euler vs RK4)
    dt_coarse = 0.08
    t_rk4, x_rk4, _ = run_open_loop_simulation(force=20.0, t_end=t_end, dt=dt_coarse, method="rk4")
    t_euler, x_euler, _ = run_open_loop_simulation(force=20.0, t_end=t_end, dt=dt_coarse, method="euler")

    # High-precision benchmark for error comparison (dt = 0.001 s with RK4)
    t_ref, x_ref, _ = run_open_loop_simulation(force=20.0, t_end=t_end, dt=0.001, method="rk4")

    # 3. Create High-Quality Figures
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=150)

    # Subplot 1: Open-loop responses
    ax1.plot(t_free, x_free, label="Free Release ($x_0=1.0\\,$m, $u=0\\,$N)", color="#1f77b4", linewidth=2.0)
    ax1.plot(t_10N, x_10N, label="Step Force $u=10\\,$N (Settles at $0.5\\,$m)", color="#ff7f0e", linewidth=2.0)
    ax1.plot(t_20N, x_20N, label="Step Force $u=20\\,$N (Settles at $1.0\\,$m)", color="#2ca02c", linewidth=2.0)

    # Reference asymptotes
    ax1.axhline(0.0, color="#1f77b4", linestyle="--", alpha=0.5)
    ax1.axhline(0.5, color="#ff7f0e", linestyle="--", alpha=0.5)
    ax1.axhline(1.0, color="#2ca02c", linestyle="--", alpha=0.5, label="Target Equilibrium ($x_{ss}=1.0\\,$m)")

    ax1.set_title("Open-Loop Dynamics: Equilibrium & Steady-State", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Time (s)", fontsize=11)
    ax1.set_ylabel("Position $x(t)$ (m)", fontsize=11)
    ax1.set_xlim([0.0, t_end])
    ax1.set_ylim([-0.05, 1.15])
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right", framealpha=0.9)

    # Subplot 2: Euler vs RK4 Integrator comparison
    ax2.plot(t_ref, x_ref, label="Benchmark Reference (RK4, $dt=0.001\\,$s)", color="black", linewidth=2.0)
    ax2.plot(t_rk4, x_rk4, "o--", label="Runge-Kutta 4 (RK4, $dt=0.08\\,$s)", color="#2ca02c", markersize=4, alpha=0.9)
    ax2.plot(t_euler, x_euler, "s-.", label="Forward Euler ($dt=0.08\\,$s)", color="#d62728", markersize=4, alpha=0.9)

    ax2.set_title("Numerical Integrator Comparison (Coarse Step $dt=0.08\\,$s)", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Time (s)", fontsize=11)
    ax2.set_ylabel("Position $x(t)$ (m)", fontsize=11)
    ax2.set_xlim([0.0, t_end])
    ax2.set_ylim([-0.05, 1.15])
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="lower right", framealpha=0.9)

    plt.tight_layout()

    # Ensure plots directory exists
    plots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plots"))
    os.makedirs(plots_dir, exist_ok=True)
    plot_path = os.path.join(plots_dir, "00_open_loop_response.png")
    plt.savefig(plot_path, dpi=200)
    plt.close()

    print(f"Plot saved successfully to: {plot_path}")
    print(f"Final position under u = 20 N: {x_20N[-1]:.4f} m (Expected: 1.0000 m)")
    print("=" * 70)


if __name__ == "__main__":
    main()
