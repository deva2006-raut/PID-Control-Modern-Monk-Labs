"""
Supporting Script: Generate Feedback Loop Block Diagram & Annotated Metrics Diagram.

Creates:
1. plots/00_feedback_loop_diagram.png: High-resolution control loop architecture diagram.
2. plots/04_annotated_metrics_definition.png: Explicitly annotated step response showing
   Rise Time (10% to 90%), Peak Overshoot (Mp), Settling Time (2% band), and Steady-State Error (ess).
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

plots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plots"))
os.makedirs(plots_dir, exist_ok=True)


def create_feedback_loop_diagram():
    """Create a publication-quality block diagram of the closed-loop system."""
    fig, ax = plt.subplots(figsize=(10, 3.6), dpi=200)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")

    # Define box styles
    bbox_ctrl = dict(boxstyle="square,pad=0.5", facecolor="#d0e1fd", edgecolor="#1f77b4", linewidth=1.5)
    bbox_act = dict(boxstyle="square,pad=0.4", facecolor="#ffe3b3", edgecolor="#ff7f0e", linewidth=1.5)
    bbox_plant = dict(boxstyle="square,pad=0.6", facecolor="#d5f5d5", edgecolor="#2ca02c", linewidth=1.5)
    bbox_sensor = dict(boxstyle="square,pad=0.4", facecolor="#f3d8f7", edgecolor="#9467bd", linewidth=1.5)

    # Summing junction
    circle = plt.Circle((1.5, 2.5), 0.25, facecolor="#ffffff", edgecolor="black", linewidth=1.5)
    ax.add_patch(circle)
    ax.text(1.5, 2.5, "+", fontsize=14, fontweight="bold", ha="center", va="center")
    ax.text(1.3, 2.1, "−", fontsize=14, fontweight="bold", ha="center", va="center")

    # Blocks
    ax.text(3.4, 2.5, "PID Controller\n$u_{cmd} = K_p e + K_i\\int e - K_d \\dot{y}$\n[Anti-Windup, Filter]",
            ha="center", va="center", bbox=bbox_ctrl, fontsize=8.5, fontweight="bold")

    ax.text(5.5, 2.5, "Actuator Saturation\n$[-30\\,\\mathrm{N}, +30\\,\\mathrm{N}]$",
            ha="center", va="center", bbox=bbox_act, fontsize=8.5, fontweight="bold")

    ax.text(7.7, 2.5, "Physical Plant\n$m\\ddot{x} + c\\dot{x} + kx = u$\n($m=1, c=10, k=20$)",
            ha="center", va="center", bbox=bbox_plant, fontsize=8.5, fontweight="bold")

    ax.text(5.5, 0.8, "Feedback Sensor\nPosition $y(t) \\pm 1\\,\\mathrm{mm}$ Noise",
            ha="center", va="center", bbox=bbox_sensor, fontsize=8.5, fontweight="bold")

    # Arrows
    arrow_kw = dict(arrowstyle="->", color="black", lw=1.5)

    # Reference input -> Summing junction
    ax.annotate("", xy=(1.25, 2.5), xytext=(0.2, 2.5), arrowprops=arrow_kw)
    ax.text(0.3, 2.7, "Setpoint $r(t) = 1.0\\,\\mathrm{m}$", fontsize=8.5, fontweight="bold")

    # Summing junction -> Controller
    ax.annotate("", xy=(2.3, 2.5), xytext=(1.75, 2.5), arrowprops=arrow_kw)
    ax.text(1.8, 2.7, "Error $e(t)$", fontsize=8.5)

    # Controller -> Saturation
    ax.annotate("", xy=(4.65, 2.5), xytext=(4.3, 2.5), arrowprops=arrow_kw)
    ax.text(4.35, 2.7, "$u_{cmd}$", fontsize=8.5)

    # Saturation -> Plant
    ax.annotate("", xy=(6.7, 2.5), xytext=(6.35, 2.5), arrowprops=arrow_kw)
    ax.text(6.4, 2.7, "$u_{actual}$", fontsize=8.5)

    # Plant -> Output
    ax.annotate("", xy=(9.7, 2.5), xytext=(8.7, 2.5), arrowprops=arrow_kw)
    ax.text(9.0, 2.7, "Position $x(t)$", fontsize=8.5, fontweight="bold")

    # Feedback tap: (8.9, 2.5) -> (8.9, 0.8) -> Sensor -> (1.5, 0.8) -> Summing junction
    ax.plot([8.9, 8.9], [2.5, 0.8], color="black", lw=1.5)
    ax.annotate("", xy=(6.7, 0.8), xytext=(8.9, 0.8), arrowprops=arrow_kw)
    ax.annotate("", xy=(1.5, 0.8), xytext=(4.3, 0.8), arrowprops=dict(arrowstyle="-", color="black", lw=1.5))
    ax.annotate("", xy=(1.5, 2.25), xytext=(1.5, 0.8), arrowprops=arrow_kw)

    plt.title("Closed-Loop Control Architecture with Hardware Non-Idealities", fontsize=11, fontweight="bold", pad=12)
    plt.tight_layout()
    diagram_path = os.path.join(plots_dir, "00_feedback_loop_diagram.png")
    plt.savefig(diagram_path, dpi=200)
    plt.close()
    print(f"Saved: {diagram_path}")


def create_annotated_metrics_diagram():
    """Create an explicitly annotated step-response plot defining tr, Mp, ts, ess."""
    t = np.linspace(0, 4.0, 2000)
    # Underdamped illustrative response
    wn = 4.0
    zeta = 0.4
    wd = wn * np.sqrt(1 - zeta**2)
    phi = np.arctan(np.sqrt(1 - zeta**2) / zeta)
    y = 1.0 - (np.exp(-zeta * wn * t) / np.sqrt(1 - zeta**2)) * np.sin(wd * t + phi)

    # Critical points
    target = 1.0
    y_10 = 0.1 * target
    y_90 = 0.9 * target
    t_10 = t[np.where(y >= y_10)[0][0]]
    t_90 = t[np.where(y >= y_90)[0][0]]
    tr = t_90 - t_10

    peak_idx = np.argmax(y)
    t_peak = t[peak_idx]
    y_peak = y[peak_idx]
    mp = (y_peak - target) * 100.0

    # 2% settling band
    band_hi = 1.02
    band_lo = 0.98
    outside = np.where((y < band_lo) | (y > band_hi))[0]
    t_s = t[outside[-1] + 1]

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=200)

    # Plot response and target
    ax.plot(t, y, color="#1f77b4", lw=2.2, label="Step Response $y(t)$")
    ax.axhline(target, color="black", linestyle="--", lw=1.5, label="Target Setpoint ($r = 1.0\\,\\mathrm{m}$)")

    # 2% Tolerance Band Shading
    ax.axhspan(band_lo, band_hi, color="#2ca02c", alpha=0.15, label="$\\pm 2\\%$ Tolerance Band ($[0.98, 1.02]$)")

    # 1. Annotate Rise Time (10% to 90%)
    ax.axhline(y_10, color="gray", linestyle=":", alpha=0.6)
    ax.axhline(y_90, color="gray", linestyle=":", alpha=0.6)
    ax.plot([t_10, t_10], [0, y_10], color="gray", linestyle=":", alpha=0.6)
    ax.plot([t_90, t_90], [0, y_90], color="gray", linestyle=":", alpha=0.6)
    ax.annotate("", xy=(t_90, 0.5), xytext=(t_10, 0.5),
                arrowprops=dict(arrowstyle="<->", color="purple", lw=1.8))
    ax.text((t_10 + t_90) / 2, 0.54, f"Rise Time $t_r = {tr:.2f}\\,\\mathrm{{s}}$\n($10\\% \\to 90\\%$)",
            ha="center", va="bottom", color="purple", fontweight="bold", fontsize=9.5)

    # 2. Annotate Overshoot (Mp)
    ax.plot([t_peak, t_peak], [target, y_peak], color="red", linestyle="-", lw=1.8)
    ax.plot(t_peak, y_peak, "ro", markersize=6)
    ax.annotate("", xy=(t_peak, y_peak), xytext=(t_peak, target),
                arrowprops=dict(arrowstyle="<->", color="red", lw=1.8))
    ax.text(t_peak + 0.08, (target + y_peak) / 2,
            f"Peak Overshoot $M_p = {mp:.1f}\\%$\n($y_{{max}} = {y_peak:.2f}\\,\\mathrm{{m}}$)",
            va="center", color="red", fontweight="bold", fontsize=9.5)

    # 3. Annotate Settling Time (ts)
    ax.axvline(t_s, color="#2ca02c", linestyle="--", lw=1.8)
    ax.annotate("", xy=(t_s, 0.2), xytext=(0, 0.2),
                arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=1.8))
    ax.text(t_s / 2, 0.23, f"Settling Time $t_s = {t_s:.2f}\\,\\mathrm{{s}}$ ($2\\%$ Band)",
            ha="center", color="#2ca02c", fontweight="bold", fontsize=9.5)

    # 4. Annotate Steady-State Error
    ax.annotate("Steady-State Error $e_{ss} = |r - y(\\infty)| \\approx 0$",
                xy=(3.5, 1.0), xytext=(2.5, 0.75),
                arrowprops=dict(arrowstyle="->", color="blue", lw=1.5),
                fontsize=9.5, fontweight="bold", color="blue")

    ax.set_title("Standard Step-Response Performance Metrics Definition", fontsize=12, fontweight="bold")
    ax.set_xlabel("Time $t$ (seconds)", fontsize=11)
    ax.set_ylabel("Controlled Output $y(t)$ (metres)", fontsize=11)
    ax.set_xlim([0, 4.0])
    ax.set_ylim([0, 1.45])
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9.5)

    plt.tight_layout()
    metrics_plot_path = os.path.join(plots_dir, "04_annotated_metrics_definition.png")
    plt.savefig(metrics_plot_path, dpi=200)
    plt.close()
    print(f"Saved: {metrics_plot_path}")


if __name__ == "__main__":
    create_feedback_loop_diagram()
    create_annotated_metrics_diagram()
