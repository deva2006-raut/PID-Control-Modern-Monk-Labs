# PID Control – Complete Technical Assignment

**Organization:** Modern Monk Labs  
**Candidate:** Devanshu Raut  
**Role:** Physical AI Research Intern  
**Topic:** Mass-Spring-Damper Simulation, Manual PID Control, Real-World Hardware Non-Idealities & Tuning  
**Technical Document:** [`report/technical_report.pdf`](report/technical_report.pdf) (15-Page Publication-Standard Report)

---

## 📖 Project Overview

In robotics and Physical AI, software algorithms must interact safely with physical mechanisms (motors, gears, springs, inertia). A **PID (Proportional-Integral-Derivative) controller** serves as the foundational feedback mechanism that drives physical systems to target states while overcoming friction, spring forces, external disturbances, and actuator limits.

This repository implements a **from-scratch, production-grade PID control suite in Python** without relying on ready-made control libraries (e.g., `scipy.signal` or `python-control`). It models a 1-DOF horizontal mass-spring-damper system governed by Newton's Second Law:

$$m \ddot{x}(t) + c \dot{x}(t) + k x(t) = u(t)$$

with exact assigned parameters:
* **Mass ($m$):** $1.0\text{ kg}$
* **Viscous Damping ($c$):** $10.0\text{ N}\cdot\text{s/m}$
* **Spring Stiffness ($k$):** $20.0\text{ N/m}$
* **Target Setpoint ($r$):** $1.0\text{ m}$
* **Actuator Force Limits:** $[-30.0\text{ N}, +30.0\text{ N}]$

---

## 📁 Repository Structure

```text
PID Control  project/
├── .gitignore                          # Excludes caches, venv, and build artifacts
├── requirements.txt                    # Pinned dependencies (numpy, matplotlib, reportlab)
├── README.md                           # This comprehensive guide and interview manual
│
├── src/                                # Core reusable modular packages
│   ├── __init__.py                     # Marks directory as a Python package
│   ├── plant.py                        # MassSpringDamper physical ODE simulator (Euler & RK4)
│   ├── controller.py                   # Industrial PIDController with anti-windup & filters
│   └── metrics.py                      # Automated step-response performance metrics (tr, Mp, ts, ess)
│
├── experiments/                        # Standalone runnable simulation experiments
│   ├── generate_diagrams.py            # Generates feedback architecture and annotated metrics plots
│   ├── 00_open_loop_plant.py           # Free decay, step inputs (10 N, 20 N), and RK4 vs Euler
│   ├── 01_baseline_controllers.py      # P, PI, PD, and Full PID comparative benchmarks
│   ├── 02_actuator_saturation.py       # Actuator ±30 N limits, Integral Windup vs Anti-Windup
│   ├── 03_sensor_noise_filtering.py    # ±1 mm sensor noise, raw vs low-pass filtered D-term
│   ├── 04_derivative_kick.py           # Setpoint step: D-on-error (+3000 N spike) vs D-on-measurement
│   ├── 05_sampling_rate_effects.py     # Discretization: 200 Hz down to 2 Hz; poorly damped at 5 Hz & 2 Hz
│   ├── 06_manual_tuning.py             # 4-stage systematic heuristic manual tuning sequence
│   └── 07_ziegler_nichols_tuning.py    # Z-N analysis: proof on ideal G(s)=1/(s+1) vs. delayed FOPDT demo
│
├── plots/                              # 13 High-resolution generated engineering figures
│   ├── 00_feedback_loop_diagram.png    # Control loop architecture block diagram
│   ├── 00_open_loop_response.png       # Open-loop physics and steady-state holding force
│   ├── 01_baseline_comparison.png      # 4-controller step response and actuator effort
│   ├── 01_p_gain_sweep.png             # P-only gain sweep verifying analytical droop formula
│   ├── 01_i_gain_sweep.png             # I-gain sweep showing steady-state error elimination
│   ├── 01_d_gain_sweep.png             # D-gain sweep showing active velocity damping
│   ├── 02_integral_windup.png          # Wound-up integrator (34.55 N) vs clamped (19.97 N)
│   ├── 03_sensor_noise_filtering.png   # 86.8% chatter reduction via 1st-order low-pass filter
│   ├── 04_annotated_metrics_definition.png # Explicit annotations of tr, Mp, ts, and ess
│   ├── 04_derivative_kick.png          # Instantaneous +3000 N spike eliminated by D-on-measurement
│   ├── 05_sampling_rate_effects.png    # ZOH delay: stable 10-200 Hz vs poorly damped at 5 Hz & 2 Hz
│   ├── 06_manual_tuning.png            # 4-stage manual tuning response progression
│   └── 07_ziegler_nichols.png          # Z-N analysis: monotonic G(s)=1/(s+1) vs oscillation on delayed FOPDT model
│
├── report/                             # Deliverable documentation
│   ├── generate_report.py              # ReportLab script compiling publication PDF
│   └── technical_report.pdf            # 15-Page final technical report
│
└── tests/                              # Automated unit tests (Python built-in unittest)
    ├── __init__.py
    ├── test_plant.py                   # 6 physics & ODE convergence tests
    ├── test_controller.py              # 9 controller safety, anti-windup, and kick tests
    └── test_metrics.py                 # 7 analytical step-response metrics tests
```

---

## 🛠️ Installation & Quickstart (Beginner-Friendly)

### 1. Prerequisites
Ensure **Python 3.10+** is installed on your machine (tested and benchmarked on Python 3.10 through Python 3.14.7). Check by running:
```powershell
python --version
```

### 2. Virtual Environment Setup (Recommended)
Open a terminal (PowerShell or Command Prompt) in the project root directory:
```powershell
# Create an isolated virtual environment
python -m venv venv

# Activate on Windows (PowerShell)
.\venv\Scripts\Activate.ps1
```
*(If PowerShell shows an execution policy error, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and re-run activate).*

### 3. Install Dependencies
The project uses **NumPy** and **Matplotlib** as external dependencies for physical simulation and plotting (and **ReportLab** for PDF compilation). Only Python's **`unittest`** runner is built in.

```powershell
pip install -r requirements.txt
```

---

## 🧪 Exact Commands to Run All Experiments & Tests

Every figure, metric, and table in this project is **100% reproducible** by running the scripts below:

### Run the Full Unit Test Suite (22 Tests)
```powershell
python -m unittest discover tests
```
*Expected Result:* `Ran 22 tests in 0.011s — OK`

### Run Individual Experiments
```powershell
# 1. Open-loop physics & 20 N holding force verification
python experiments/00_open_loop_plant.py

# 2. Baseline comparison (P, PI, PD, Full PID) & metrics table
python experiments/01_baseline_controllers.py

# 3. Actuator saturation & integral windup demonstration
python experiments/02_actuator_saturation.py

# 4. Sensor noise (±1 mm) & low-pass derivative filtering
python experiments/03_sensor_noise_filtering.py

# 5. Derivative kick elimination via derivative-on-measurement
python experiments/04_derivative_kick.py

# 6. Sampling rate & discretization limits (poorly damped at 5 Hz and 2 Hz)
python experiments/05_sampling_rate_effects.py

# 7. Heuristic manual tuning sequence
python experiments/06_manual_tuning.py

# 8. Ziegler-Nichols analysis: proof on ideal G(s)=1/(s+1) vs. delayed FOPDT demonstration
python experiments/07_ziegler_nichols_tuning.py

# 9. Generate supporting architecture and annotated metrics diagrams
python experiments/generate_diagrams.py

# 10. Compile the 15-page Technical PDF Report
python report/generate_report.py
```

---

## 📊 Summary of Verified Numerical Results

### 1. Steady-State Equilibrium & P-Control Droop Verification
* **Why 20 N is required at $1.0\text{ m}$:** In steady state ($\dot{x}=0, \ddot{x}=0$), Newton's law reduces to $k \cdot x_{\text{ss}} = u_{\text{ss}} \implies 20.0 \times 1.0 = \mathbf{20.0\text{ N}}$.
* **Why pure P-control stops short:** $x_{\text{analytical}} = \frac{K_p}{K_p + k} \cdot r = \frac{K_p}{K_p + 20} < 1.0\text{ m}$.
* **Numerical Match:** Simulated RK4 positions matched theory with **$0.000000\text{ m}$ discrepancy**:
  - $K_p = 20\text{ N/m} \implies x = 0.5000\text{ m}$ ($50.0\%$ error)
  - $K_p = 50\text{ N/m} \implies x = 0.7143\text{ m}$ ($28.6\%$ error)
  - $K_p = 100\text{ N/m} \implies x = 0.8333\text{ m}$ ($16.7\%$ error)
  - $K_p = 200\text{ N/m} \implies x = 0.9091\text{ m}$ ($9.1\%$ error)

### 2. Master Baseline Controller Benchmark ($u_{\text{limit}} = \pm 30\text{ N}$)
| Controller | Gains $(K_p, K_i, K_d)$ | Rise Time $t_r$ ($10\%\to 90\%$) | Overshoot $M_p$ ($\%$) | Settling Time $t_s$ ($2\%$) | Steady-State Error $e_{\text{ss}}$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **P Controller** | $(100, 0, 0)$ | **N/A\*** | $0.00\%$ | **N/A\*\*** | $0.1667\text{ m}$ |
| **PI Controller** | $(100, 80, 0)$ | $0.435\text{ s}$ | $0.00\%$ | $3.505\text{ s}$ | $0.0038\text{ m}$ |
| **PD Controller** | $(100, 0, 15)$ | **N/A\*** | $0.00\%$ | **N/A\*\*** | $0.1667\text{ m}$ |
| **Full PID Controller** | $(100, 80, 15)$ | $0.695\text{ s}$ | $0.00\%$ | **2.435 s** | **0.0013 m** |

*\* N/A: Never reaches $90\%$ of setpoint due to steady-state droop.*  
*\*\* N/A: Never enters $\pm 2\%$ tolerance corridor $[0.98\text{ m}, 1.02\text{ m}]$.*

### 3. Real-World Hardware Defenses
* **Integral Anti-Windup:** Without anti-windup, the integrator wound up to $+34.55\text{ N}$, causing **$12.90\%$ overshoot**. With conditional clamping, the integrator was held at $19.97\text{ N}$, achieving **$0.00\%$ overshoot**.
* **Sensor Noise ($\pm 1\text{ mm}$):** The noise difference between consecutive samples $\Delta \eta = \eta[k] - \eta[k-1]$ depends on both samples and can reach up to $\pm 2\text{ mm}$ ($\pm 0.002\text{ m}$), generating discrete pseudo-velocity noise up to $\pm 0.40\text{ m/s}$ and theoretical derivative force spikes up to $\pm 6.0\text{ N}$ (empirical simulation: peak $|D| = 5.80\text{ N}$, $\sigma_u = 2.54\text{ N}$). Inserting a discrete 1st-order low-pass filter ($\tau_f = 0.03\text{ s}$, cutoff frequency $f_c \approx 5.3\text{ Hz}$ and $\omega_c \approx 33.3\text{ rad/s}$) achieved an **$86.8\%$ reduction in chatter** ($\sigma_u = 0.33\text{ N}$).
* **Derivative Kick:** In a discrete controller with $\Delta t = 0.005\text{ s}$, a $1\text{ m}$ step setpoint change produces a finite sampled error derivative of $200\text{ m/s}$, commanding a theoretical unconstrained derivative force of **$+3000.0\text{ N}$**. While actual applied motor force is clamped to $\pm 30\text{ N}$, this command saturates the actuator in a single $5\text{ ms}$ step. Differentiating measurement completely eliminated the initial spike (**$0.0\text{ N}$ kick**).
* **Sampling Rate Stability Threshold:** The system is rock-solid from $200\text{ Hz}$ down to $10\text{ Hz}$. At $5\text{ Hz}$ ($T_s = 200\text{ ms}$) and $2\text{ Hz}$ ($T_s = 500\text{ ms}$), Zero-Order Hold phase lag erodes phase margin; the response becomes poorly damped and does not settle within the simulation window.

### 4. Ziegler-Nichols Analysis: Assigned Ideal Plant vs. Additional Delayed FOPDT Demonstration

A key control engineering insight demonstrated in this project is that **textbook Ziegler-Nichols oscillation tuning cannot be naively applied to every transfer function**. We rigorously distinguish the assigned ideal plant from the delayed demonstration model:

| Comparative Dimension | Assigned Ideal System $G(s) = \frac{1}{s+1}$ | Additional Delayed System $G_{\text{FOPDT}}(s) = \frac{e^{-0.2s}}{s+1}$ |
| :--- | :--- | :--- |
| **Project Role** | **Mandatory assignment requirement** | **Additional engineering demonstration** |
| **Transport Dead Time ($L$)** | $L = 0.0\text{ s}$ (Ideal continuous system) | $L = 0.2\text{ s}$ (Realistic hardware latency) |
| **Frequency Phase Response** | $\angle G(j\omega) = -\arctan(\omega) \in [0^\circ, -90^\circ)$ | $\angle G(j\omega) = -\arctan(\omega) - 0.2\omega$ (reaches $-180^\circ$) |
| **Phase Crossover Frequency** | **Does not exist** (phase never reaches $-180^\circ$) | $\omega_u = 8.443\text{ rad/s}$ ($P_u = 0.744\text{ s}$) |
| **Ultimate Gain / Gain Margin** | **Infinite Gain Margin** ($K_u = \infty$) | **Finite Ultimate Gain** ($K_u = 8.502$) |
| **P-Control Behavior** | Strictly monotonic exponential step response; **sustained oscillations are mathematically impossible** | Reaches sustained marginal oscillation at $K_p = K_u = 8.502$ |
| **Z-N Frequency Tuning** | **Undefined / Inapplicable** under continuous pure P-control | **Applicable**: Classic Z-N yields $(K_p=5.101, K_i=13.711, K_d=0.475)$ |
| **Closed-Loop Poles** | Single pole at $s = -(1 + K_p) < 0$ for all finite $K_p > 0$ | Infinite spectrum of poles due to quasi-polynomial; crossed into RHP if $K_p > 8.502$ |
| **Modern Engineering Refinement** | Refined manual tuning $(K_p=100, K_i=80, K_d=15)$ on mass-spring-damper | Conservative detuning $(K_p=3.0, K_i=4.0, K_d=0.35)$ limits overshoot from $54.2\%$ to $11.8\%$ |

---

## 🎯 Technical Interview Cheat Sheet (Q&A Preparation)

When Modern Monk Labs reviewers ask you about this project in a technical interview, use these precise explanations:

1. **Q: Why does proportional control always leave steady-state error on this mass-spring-damper?**  
   * **A:** "Because Hooke's spring opposes displacement: $F_{\text{spring}} = k \cdot x$. At steady state, velocity and acceleration are zero, so $K_p (r - x_{\text{ss}}) = k \cdot x_{\text{ss}}$, which yields $x_{\text{ss}} = \frac{K_p}{K_p + k} r$. For any finite $K_p$, this ratio is strictly less than 1. If error ever reached zero, the proportional force would be zero, and the spring would instantly pull the mass back. Integral action is mathematically required to store the $20\text{ N}$ holding force while error is zero."

2. **Q: What are the physical units of $K_p$, $K_i$, and $K_d$?**  
   * **A:** "$K_p$ is in $\text{N/m}$, which has the exact same dimensions as spring stiffness ($k$), acting as an artificial software spring. $K_d$ is in $\text{N}\cdot\text{s/m}$, which has the same dimensions as viscous damping ($c$), acting as an artificial shock absorber. $K_i$ is in $\text{N}/(\text{m}\cdot\text{s})$, representing accumulated force over integrated error."

3. **Q: What is Integral Windup and how did you prevent it?**  
   * **A:** "When the actuator saturates at $+30\text{ N}$, the physical plant cannot accelerate any faster. A naive integrator keeps accumulating positive error, winding up to $+34.55\text{ N}$. When the cart crosses the setpoint, the actuator remains pinned at $+30\text{ N}$ until the excess charge unwinds, causing massive overshoot. We solved this with **conditional clamping**: if the unconstrained control signal exceeds $\pm 30\text{ N}$ and error has the same sign, we freeze integration."

4. **Q: What is Derivative Kick and how do you solve it?**  
   * **A:** "In a discrete controller with sampling interval $\Delta t = 0.005\text{ s}$, a $1\text{ m}$ step change in setpoint produces a finite sampled derivative of $\frac{\Delta e}{\Delta t} = \frac{1.0}{0.005} = 200\text{ m/s}$. With $K_d = 15\text{ N}\cdot\text{s/m}$, this commands an unconstrained theoretical derivative force of $15 \times 200 = +3000\text{ N}$. While the actual applied physical force is clamped to $+30\text{ N}$, this sudden jump saturates the actuator in a single time step ($5\text{ ms}$), creating severe mechanical shock. We solve this by computing the derivative on measurement: $-K_d \frac{dy}{dt}$. Because mass has inertia, position cannot change discontinuously, eliminating the kick completely ($0\text{ N}$ initial derivative force) while retaining full damping as the cart moves."

5. **Q: Why does slow sampling degrade performance?**  
   * **A:** "A digital controller samples at $T_s$ and holds its output constant using a Zero-Order Hold (ZOH). A ZOH introduces an average time delay of $T_{\text{delay}} \approx T_s / 2$. In the frequency domain, delay introduces phase lag: $\Delta \phi = -\omega \frac{T_s}{2}$. As sampling slows to $5\text{ Hz}$ or $2\text{ Hz}$, this phase lag severely erodes the phase margin; the response becomes poorly damped and does not settle within the simulation window."

6. **Q: Can you apply Ziegler-Nichols Ultimate Gain to the assigned plant $G(s) = \frac{1}{s+1}$?**  
   * **A:** "On the assigned ideal continuous plant $G(s) = \frac{1}{s+1}$, sustained oscillations are mathematically impossible under continuous pure proportional control because the phase lag is bounded between $0^\circ$ and $-90^\circ$. It never crosses $-180^\circ$, meaning it has an infinite gain margin and no finite ultimate gain $K_u$. However, in any physical or digital system, latency exists. To demonstrate Z-N mechanics, we conducted an additional demonstration using a delayed FOPDT system ($G(s) = \frac{e^{-0.2s}}{s + 1}$). With $L = 0.2\text{ s}$ and $\tau = 1.0\text{ s}$, phase crossover occurs at $\omega_u = 8.443\text{ rad/s}$, producing a genuine finite $K_u = 8.502$ and $P_u = 0.744\text{ s}$."

---

## 📜 AI Usage & Academic Integrity Disclosure

Antigravity AI was used extensively to generate and organize the Python implementation, experiment scripts, plots, and draft report. The candidate did not independently author or audit every component. The included automated tests and experiment scripts were rerun in a Python execution environment as part of a separate software review. These checks demonstrate software and simulation execution only and are not a substitute for independent engineering review or validation on physical hardware. The candidate is reviewing the implementation, assumptions, and limitations before technical evaluation.
