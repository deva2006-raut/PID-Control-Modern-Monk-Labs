"""
Experiment 04: Derivative Kick Elimination via Derivative-on-Measurement.

Demonstrates:
1. Derivative Kick Phenomenon (Derivative on Error):
   - Traditional PID formula differentiates error: e(t) = r(t) - y(t).
   - In a discrete-time controller with sampling interval dt = 0.005 s, an abrupt 1.0 m step
     in setpoint produces a finite sampled error derivative of:
         Delta e / Delta t = (1.0 - 0.0) / 0.005 s = 200.0 m/s.
   - Multiplying by Kd = 15 N*s/m commands an unconstrained theoretical derivative force:
         D_cmd = 15 * 200.0 = +3000.0 N.
   - While the actual motor force applied to the physical cart is clamped to [-30 N, +30 N],
     this command instantly saturates the actuator in a single 5 ms step, causing
     mechanical shock, gear-train wear, and high electrical current spikes.
2. Derivative-on-Measurement Solution:
   - Evaluates the derivative on the negative rate of position feedback: -dy/dt.
   - Because physical cart inertia prevents displacement from changing discontinuously,
     the derivative command at the step instant is exactly 0.0 N (zero kick!).
   - Once the cart begins moving, derivative-on-measurement provides smooth, identical
     braking damping without actuator shock.

Output Plot:
    plots/04_derivative_kick.png
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Ensure root directory is on sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.plant import MassSpringDamper
from src.controller import PIDController


def run_kick_simulation(
    derivative_on_measurement: bool,
    unconstrained: bool = False,
    t_end: float = 3.0,
    dt: float = 0.005,
    step_time: float = 1.0,
):
    """
    Run closed-loop simulation with a step setpoint change occurring at step_time.

    Returns
    -------
    t, target_profile, position, u_force, d_term
    """
    plant = MassSpringDamper(mass=1.0, damping=10.0, stiffness=20.0)
    limits = (-10000.0, 10000.0) if unconstrained else (-30.0, 30.0)

    controller = PIDController(
        kp=100.0,
        ki=80.0,
        kd=15.0,
        output_limits=limits,
        derivative_on_measurement=derivative_on_measurement,
        anti_windup=True,
    )

    n_steps = int(np.round(t_end / dt)) + 1
    t = np.linspace(0.0, t_end, n_steps)
    target = np.where(t >= step_time, 1.0, 0.0)

    x = np.zeros(n_steps)
    u = np.zeros(n_steps)
    d = np.zeros(n_steps)

    for idx in range(1, n_steps):
        r = target[idx]
        y = plant.position
        u_force = controller.update(setpoint=r, measurement=y, dt=dt)
        plant.step(force=u_force, dt=dt, method="rk4")

        x[idx] = plant.position
        u[idx] = u_force
        d[idx] = controller.last_d

    u[0] = u[1]
    d[0] = d[1]

    return t, target, x, u, d


def main():
    print("=" * 80)
    print("EXPERIMENT 04: DERIVATIVE KICK & DERIVATIVE-ON-MEASUREMENT EVALUATION")
    print("=" * 80)

    dt = 0.005
    step_time = 1.0

    # 1. Simulate unconstrained responses to measure the theoretical raw kick
    t, r_profile, x_err_uncon, u_err_uncon, d_err_uncon = run_kick_simulation(
        derivative_on_measurement=False, unconstrained=True, dt=dt, step_time=step_time
    )
    _, _, x_meas_uncon, u_meas_uncon, d_meas_uncon = run_kick_simulation(
        derivative_on_measurement=True, unconstrained=True, dt=dt, step_time=step_time
    )

    # 2. Simulate physically constrained responses (+/- 30 N actuator limits)
    _, _, x_err_sat, u_err_sat, d_err_sat = run_kick_simulation(
        derivative_on_measurement=False, unconstrained=False, dt=dt, step_time=step_time
    )
    _, _, x_meas_sat, u_meas_sat, d_meas_sat = run_kick_simulation(
        derivative_on_measurement=True, unconstrained=False, dt=dt, step_time=step_time
    )

    # 3. Compute Peak Values at the Step Instant
    step_idx = np.where(t >= step_time)[0][0]
    peak_kick_unconstrained = float(d_err_uncon[step_idx])
    peak_d_measurement = float(np.max(np.abs(d_meas_uncon)))

    print(f"\nAt step transition t = {step_time:.2f} s (dt = {dt*1000:.1f} ms, Kd = 15 N*s/m):")
    print(f"  • Finite Sampled Error Derivative:             {(1.0/dt):.1f} m/s  (Delta e / Delta t)")
    print(f"  • Theoretical Unconstrained Derivative Command: +{peak_kick_unconstrained:.1f} N  (15 * 200 m/s)")
    print(f"  • Actual Applied Motor Force (Clamped):         +30.0 N  (Hard physical limit)")
    print(f"  • Derivative on Measurement (at step instant):    {d_meas_uncon[step_idx]:.1f} N   (Zero initial kick!)")
    print(f"  • Derivative on Measurement (peak dynamic force): -{peak_d_measurement:.1f} N   (Smooth braking as cart moves)")
    print("-" * 80)

    # 4. Create High-Quality 3-Panel Plot
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 9), dpi=150, sharex=True)

    # Panel 1: Setpoint Step and Position Tracking
    ax1.plot(t, r_profile, "k--", label="Target Setpoint $r(t)$ (Step at $t=1.0\\,$s)", linewidth=1.5)
    ax1.plot(t, x_err_sat, label="Derivative on Error (with Saturation)", color="#d62728", linewidth=1.8)
    ax1.plot(t, x_meas_sat, label="Derivative on Measurement (Smooth)", color="#2ca02c", linewidth=2.0)
    ax1.set_ylabel("Position $x(t)$ (m)", fontsize=11)
    ax1.set_ylim([-0.05, 1.15])
    ax1.set_title("Derivative Kick Elimination via Derivative-on-Measurement", fontsize=12, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="lower right", framealpha=0.9)

    # Panel 2: Derivative Term D(t) Showing Theoretical Kick Spike
    ax2.plot(t, d_err_uncon, label=f"D-on-Error Theoretical Command (Finite Sampled Spike: +{peak_kick_unconstrained:.0f} N)", color="#d62728", linewidth=1.8)
    ax2.plot(t, d_meas_uncon, label="D-on-Measurement (Smooth, Zero Kick at Step Instant)", color="#2ca02c", linewidth=2.0)
    ax2.set_ylabel("Derivative Force $D(t)$ (N)", fontsize=11)
    ax2.set_ylim([-60.0, 3100.0])
    ax2.set_title("Theoretical Unconstrained Derivative Command $D(t)$ (+3000 N)", fontsize=11, fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper right", framealpha=0.9)

    # Panel 3: Constrained Actuator Control Force u(t) (+/- 30 N)
    ax3.plot(t, u_err_sat, label="D-on-Error Applied Force (Saturates Actuator to +30 N Limit in 5 ms)", color="#d62728", linewidth=1.8)
    ax3.plot(t, u_meas_sat, label="D-on-Measurement Applied Force (Controlled Trajectory)", color="#2ca02c", linewidth=2.0)
    ax3.axhline(30.0, color="crimson", linestyle="--", label="Actuator Limits ($\\pm 30\\,$N)")
    ax3.axhline(-30.0, color="crimson", linestyle="--")
    ax3.axhline(20.0, color="black", linestyle=":", label="Equilibrium Force ($20\\,$N)")
    ax3.set_xlabel("Time (s)", fontsize=11)
    ax3.set_ylabel("Force $u(t)$ (N)", fontsize=11)
    ax3.set_xlim([0.0, t[-1]])
    ax3.set_ylim([-35.0, 35.0])
    ax3.grid(True, linestyle=":", alpha=0.6)
    ax3.legend(loc="upper right", framealpha=0.9)

    plt.tight_layout()

    plots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plots"))
    plot_path = os.path.join(plots_dir, "04_derivative_kick.png")
    plt.savefig(plot_path, dpi=200)
    plt.close()

    print(f"\nPlot successfully saved to: {plot_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
