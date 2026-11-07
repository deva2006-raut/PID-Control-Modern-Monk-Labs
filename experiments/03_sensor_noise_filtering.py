"""
Experiment 03: Sensor Noise and First-Order Derivative Low-Pass Filtering.

Demonstrates:
1. Real-world sensor noise: Position feedback corrupted with +/- 1 mm (+/- 0.001 m) noise.
2. Raw Derivative (filter_tau = 0.0 s):
   - Discrete differentiation: Delta y_meas / Delta t.
   - The noise difference between consecutive samples Delta_eta = eta[k] - eta[k-1] depends
     on both samples. For eta in [-0.001 m, +0.001 m], Delta_eta can reach up to +/- 0.002 m (2 mm).
   - Dividing by dt = 0.005 s yields discrete pseudo-velocity noise up to +/- 0.40 m/s!
   - Multiplying by Kd = 15 N*s/m generates derivative command spikes up to +/- 6.0 N
     (verified in simulation: peak |D| = 5.799 N, force std dev sigma_u = 2.544 N).
3. Filtered Derivative (filter_tau = 0.03 s):
   - First-order discrete low-pass filter H(s) = 1 / (1 + tau*s) with cutoff frequency
     fc ≈ 5.3 Hz and omega_c ≈ 33.3 rad/s (fc = 1 / (2*pi*tau), omega_c = 1 / tau).
   - Drastically attenuates high-frequency noise while preserving true motion dynamics.

Output Plot:
    plots/03_sensor_noise_filtering.png
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Ensure root directory is on sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.plant import MassSpringDamper
from src.controller import PIDController


def run_noise_simulation(filter_tau: float, seed: int = 42, t_end: float = 4.0, dt: float = 0.005):
    """
    Run closed-loop simulation with simulated +/- 1 mm sensor noise.

    Returns
    -------
    t, true_x, noisy_meas, u, d_term
    """
    rng = np.random.default_rng(seed)
    plant = MassSpringDamper(mass=1.0, damping=10.0, stiffness=20.0)
    controller = PIDController(
        kp=100.0,
        ki=80.0,
        kd=15.0,
        filter_tau=filter_tau,
        output_limits=(-30.0, 30.0),
        derivative_on_measurement=True,
        anti_windup=True,
    )

    n_steps = int(np.round(t_end / dt)) + 1
    t = np.linspace(0.0, t_end, n_steps)
    true_x = np.zeros(n_steps)
    noisy_meas = np.zeros(n_steps)
    u = np.zeros(n_steps)
    d_term = np.zeros(n_steps)

    target = 1.0

    for idx in range(1, n_steps):
        # Physical position
        x_actual = plant.position

        # Add +/- 1 mm uniform noise (sensor uncertainty)
        noise = rng.uniform(-0.001, 0.001)
        y_sensor = x_actual + noise

        u_force = controller.update(setpoint=target, measurement=y_sensor, dt=dt)
        plant.step(force=u_force, dt=dt, method="rk4")

        true_x[idx] = plant.position
        noisy_meas[idx] = y_sensor
        u[idx] = u_force
        d_term[idx] = controller.last_d

    u[0] = u[1]
    d_term[0] = d_term[1]
    noisy_meas[0] = true_x[0]

    return t, true_x, noisy_meas, u, d_term


def main():
    print("=" * 80)
    print("EXPERIMENT 03: SENSOR NOISE & DERIVATIVE FILTERING EVALUATION")
    print("=" * 80)

    # 1. Run Simulations (Seed = 42 for strict reproducibility)
    seed = 42
    t, x_raw, y_meas_raw, u_raw, d_raw = run_noise_simulation(filter_tau=0.0, seed=seed)
    _, x_filt, y_meas_filt, u_filt, d_filt = run_noise_simulation(filter_tau=0.03, seed=seed)

    # 2. Compute Quantitative Chatter Statistics in Steady-State (Last 2 seconds)
    steady_idx = int(2.0 / 0.005)
    std_u_raw = float(np.std(u_raw[-steady_idx:]))
    std_u_filt = float(np.std(u_filt[-steady_idx:]))
    peak_d_raw = float(np.max(np.abs(d_raw[-steady_idx:])))
    peak_d_filt = float(np.max(np.abs(d_filt[-steady_idx:])))

    chatter_reduction_pct = (1.0 - (std_u_filt / std_u_raw)) * 100.0

    print(f"{'Metric (Steady-State t in [2s, 4s])':<35} | {'Raw Derivative (tau=0)':<22} | {'Filtered Derivative (tau=0.03s, fc ~= 5.3 Hz, wc ~= 33.3 rad/s)':<55}")
    print("-" * 115)
    print(f"{'Actuator Chatter Std Dev (sigma_u)':<35} | {std_u_raw:<22.3f} N | {std_u_filt:<30.3f} N")
    print(f"{'Peak Derivative Magnitude (|D|_max)':<35} | {peak_d_raw:<22.3f} N | {peak_d_filt:<30.3f} N")
    print(f"{'Actuator Chatter Reduction':<35} | {'Baseline':<22} | {chatter_reduction_pct:<30.1f}%")
    print("-" * 115)

    # 3. Create High-Quality 3-Panel Plot
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 9), dpi=150, sharex=True)

    # Panel 1: Position and Sensor Noise
    ax1.plot(t, x_raw, label="True Position (Raw D)", color="#d62728", linewidth=1.8)
    ax1.plot(t, x_filt, label="True Position (Filtered D, $\\tau=0.03\\,$s, $f_c \\approx 5.3\\,$Hz, $\\omega_c \\approx 33.3\\,$rad/s)", color="#2ca02c", linewidth=2.0)
    ax1.plot(t, y_meas_filt, label="Noisy Sensor Feedback ($x \\pm 1\\,$mm)", color="gray", alpha=0.35, linewidth=0.8)
    ax1.axhline(1.0, color="black", linestyle="--", label="Target ($1.0\\,$m)")
    ax1.set_ylabel("Position (m)", fontsize=11)
    ax1.set_ylim([0.0, 1.15])
    ax1.set_title("Sensor Noise ($\\pm 1\\,$mm) and Derivative Filtering", fontsize=12, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="lower right", framealpha=0.9)

    # Panel 2: Derivative Term Comparison (Showing Chatter)
    ax2.plot(t, d_raw, label=f"Raw Derivative Term (Peak: {peak_d_raw:.2f} N)", color="#d62728", alpha=0.7, linewidth=1.0)
    ax2.plot(t, d_filt, label=f"Filtered Derivative Term (Peak: {peak_d_filt:.2f} N)", color="#2ca02c", linewidth=2.0)
    ax2.set_ylabel("Derivative Force $D(t)$ (N)", fontsize=11)
    ax2.set_ylim([-8.0, 8.0])
    ax2.set_title("Derivative Force Chatter: Raw vs. Filtered", fontsize=11, fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper right", framealpha=0.9)

    # Panel 3: Total Actuator Force u(t)
    ax3.plot(t, u_raw, label=f"Raw Control Force ($\\sigma_u={std_u_raw:.2f}\\,$N)", color="#d62728", alpha=0.6, linewidth=1.0)
    ax3.plot(t, u_filt, label=f"Filtered Control Force ($\\sigma_u={std_u_filt:.2f}\\,$N, -{chatter_reduction_pct:.0f}%)", color="#2ca02c", linewidth=2.0)
    ax3.axhline(20.0, color="black", linestyle=":", label="Equilibrium Force ($20\\,$N)")
    ax3.set_xlabel("Time (s)", fontsize=11)
    ax3.set_ylabel("Actuator Force $u(t)$ (N)", fontsize=11)
    ax3.set_xlim([0.0, t[-1]])
    ax3.set_ylim([10.0, 32.0])
    ax3.grid(True, linestyle=":", alpha=0.6)
    ax3.legend(loc="lower right", framealpha=0.9)

    plt.tight_layout()

    plots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plots"))
    plot_path = os.path.join(plots_dir, "03_sensor_noise_filtering.png")
    plt.savefig(plot_path, dpi=200)
    plt.close()

    print(f"\nPlot successfully saved to: {plot_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
