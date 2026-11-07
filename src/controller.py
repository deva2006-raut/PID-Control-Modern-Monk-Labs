"""
PID Controller: Production-Grade Implementation for Physical AI & Robotics.

This module implements a modular, industrial-grade Proportional-Integral-Derivative
(PID) controller from scratch.

Mathematical Formula:
    u(t) = Kp * e(t) + Ki * integral(e(tau) dtau) + Kd * (de(t) / dt)

Key Engineering Features:
1. Configurable Gains: Kp, Ki, Kd with dimensional consistency.
2. Anti-Windup Clamping: Prevents integral accumulator from blowing up during
   actuator saturation (limits: [-30 N, +30 N]).
3. Derivative-on-Measurement: Eliminates "Derivative Kick" during sudden step
   changes in the reference setpoint by computing d(-y)/dt instead of de/dt.
4. First-Order Derivative Low-Pass Filter: Attenuates high-frequency sensor noise
   from corrupting actuator control signals.
5. State Reset & Input Guardrails: Robust exception handling for invalid time steps
   and saturated limit bounds.

Physical Units:
    - Error e(t)               : [m] (metres)
    - Target r(t), Position y(t): [m] (metres)
    - Proportional Gain Kp     : [N / m] (acts as an artificial spring)
    - Integral Gain Ki         : [N / (m * s)] (accumulates persistent offset)
    - Derivative Gain Kd       : [N * s / m] (acts as an artificial damper)
    - Control Output u(t)      : [N] (Newtons)
"""

from typing import Optional, Dict


class PIDController:
    """
    A robust, discrete-time PID Controller with anti-windup and derivative filtering.

    Parameters
    ----------
    kp : float
        Proportional gain [N/m]. Must be non-negative.
    ki : float
        Integral gain [N/(m*s)]. Must be non-negative.
    kd : float
        Derivative gain [N*s/m]. Must be non-negative.
    output_limits : tuple of (float, float), default=(-30.0, 30.0)
        Minimum and maximum actuator output force [N].
    filter_tau : float, default=0.0
        Derivative low-pass filter time constant [s].
        - If tau == 0: Filter is disabled (pure derivative).
        - If tau > 0 : Filters noise with cutoff frequency fc ≈ 5.3 Hz and
          omega_c ≈ 33.3 rad/s (for tau = 0.03 s). In general, omega_c = 1 / tau [rad/s]
          and fc = 1 / (2 * pi * tau) [Hz].
    derivative_on_measurement : bool, default=True
        - If True: Computes derivative of measurement (-dy/dt) to eliminate derivative kick.
        - If False: Computes derivative of error (de/dt).
    anti_windup : bool, default=True
        - If True: Enables conditional integration / clamping to stop integral windup.
    """

    def __init__(
        self,
        kp: float = 0.0,
        ki: float = 0.0,
        kd: float = 0.0,
        output_limits: tuple[float, float] = (-30.0, 30.0),
        filter_tau: float = 0.0,
        derivative_on_measurement: bool = True,
        anti_windup: bool = True,
    ) -> None:
        # Validate gains
        if kp < 0.0 or ki < 0.0 or kd < 0.0:
            raise ValueError(f"Gains must be non-negative. Got kp={kp}, ki={ki}, kd={kd}.")

        # Validate saturation limits
        u_min, u_max = output_limits
        if u_min >= u_max:
            raise ValueError(
                f"Minimum limit ({u_min}) must be strictly less than maximum limit ({u_max})."
            )

        if filter_tau < 0.0:
            raise ValueError(f"Filter time constant filter_tau must be >= 0. Got {filter_tau}.")

        self.kp: float = float(kp)
        self.ki: float = float(ki)
        self.kd: float = float(kd)
        self.u_min: float = float(u_min)
        self.u_max: float = float(u_max)
        self.filter_tau: float = float(filter_tau)
        self.derivative_on_measurement: bool = bool(derivative_on_measurement)
        self.anti_windup: bool = bool(anti_windup)

        # Internal controller state
        self.integral: float = 0.0
        self.prev_error: Optional[float] = None
        self.prev_measurement: Optional[float] = None
        self.filtered_derivative: float = 0.0

        # Diagnostics for tracking and telemetry
        self.last_p: float = 0.0
        self.last_i: float = 0.0
        self.last_d: float = 0.0
        self.last_unconstrained: float = 0.0
        self.last_output: float = 0.0
        self.is_saturated: bool = False

    def reset(self) -> None:
        """Reset internal memory (integrator, previous states, and filter)."""
        self.integral = 0.0
        self.prev_error = None
        self.prev_measurement = None
        self.filtered_derivative = 0.0
        self.last_p = 0.0
        self.last_i = 0.0
        self.last_d = 0.0
        self.last_unconstrained = 0.0
        self.last_output = 0.0
        self.is_saturated = False

    def update(self, setpoint: float, measurement: float, dt: float) -> float:
        """
        Compute control output u(t) given current setpoint and measurement.

        Parameters
        ----------
        setpoint : float
            Desired target state r(t) [m].
        measurement : float
            Current measured feedback state y(t) [m].
        dt : float
            Elapsed time step since last update [s]. Must be strictly positive.

        Returns
        -------
        output : float
            Saturated control force u(t) [N] clamped to [u_min, u_max].
        """
        if dt <= 0.0:
            raise ValueError(f"Time step dt must be strictly positive (> 0), got {dt} s.")

        # 1. Error calculation: e(t) = r(t) - y(t)
        error = float(setpoint) - float(measurement)

        # -------------------------------------------------------------
        # 2. PROPORTIONAL TERM: P(t) = Kp * e(t)
        # -------------------------------------------------------------
        p_term = self.kp * error

        # -------------------------------------------------------------
        # 3. DERIVATIVE TERM: D(t)
        # -------------------------------------------------------------
        # Derivative kick prevention:
        # If setpoint steps discontinuously, de/dt produces a Dirac delta spike.
        # Since e = r - y, de/dt = dr/dt - dy/dt.
        # Assuming piecewise constant setpoint (dr/dt = 0), de/dt = -dy/dt.
        if self.derivative_on_measurement:
            if self.prev_measurement is None:
                raw_derivative = 0.0
            else:
                raw_derivative = -(float(measurement) - self.prev_measurement) / dt
        else:
            if self.prev_error is None:
                raw_derivative = 0.0
            else:
                raw_derivative = (error - self.prev_error) / dt

        # First-Order Low-Pass Filter on Derivative:
        # Discrete formulation of H(s) = 1 / (1 + tau * s):
        #   d_filtered[k] = alpha * d_filtered[k-1] + (1 - alpha) * d_raw[k]
        # where alpha = tau / (tau + dt).
        if self.filter_tau > 0.0:
            alpha = self.filter_tau / (self.filter_tau + dt)
            if self.prev_measurement is None and self.prev_error is None:
                # Initialize filter on the first step to avoid transient lag
                self.filtered_derivative = raw_derivative
            else:
                self.filtered_derivative = (alpha * self.filtered_derivative) + ((1.0 - alpha) * raw_derivative)
            derivative_value = self.filtered_derivative
        else:
            self.filtered_derivative = raw_derivative
            derivative_value = raw_derivative

        d_term = self.kd * derivative_value

        # -------------------------------------------------------------
        # 4. INTEGRAL TERM: I(t) & ANTI-WINDUP CLAMPING
        # -------------------------------------------------------------
        # Tentative integration step: Rectangular numerical integration
        # I_candidate = I_prev + Ki * error * dt
        delta_integral = self.ki * error * dt
        tentative_integral = self.integral + delta_integral

        # Unconstrained candidate control output
        unconstrained_output = p_term + tentative_integral + d_term

        # Anti-windup conditional integration (clamping):
        # If the actuator is saturated, and the new integration step would push
        # the actuator even deeper into saturation, FREEZE the integrator.
        if self.anti_windup:
            pushing_positive = (unconstrained_output > self.u_max) and (error > 0.0)
            pushing_negative = (unconstrained_output < self.u_min) and (error < 0.0)

            if pushing_positive or pushing_negative:
                # Do not accumulate integral; keep previous integral value
                i_term = self.integral
            else:
                # Safe to accumulate
                self.integral = tentative_integral
                # Also clamp the integral term itself so it never exceeds actuator bounds
                self.integral = max(self.u_min, min(self.integral, self.u_max))
                i_term = self.integral
        else:
            # Naive accumulation (windup allowed)
            self.integral = tentative_integral
            i_term = self.integral

        # -------------------------------------------------------------
        # 5. TOTAL CONTROL OUTPUT & SATURATION
        # -------------------------------------------------------------
        u_unconstrained = p_term + i_term + d_term

        # Clamp output to physical actuator limits [-30 N, +30 N]
        u_saturated = max(self.u_min, min(u_unconstrained, self.u_max))

        # Store diagnostics for telemetry and plotting
        self.last_p = p_term
        self.last_i = i_term
        self.last_d = d_term
        self.last_unconstrained = u_unconstrained
        self.last_output = u_saturated
        self.is_saturated = (u_unconstrained != u_saturated)

        # Update historical memory for next step
        self.prev_error = error
        self.prev_measurement = float(measurement)

        return u_saturated

    def get_components(self) -> Dict[str, float]:
        """Return instantaneous P, I, D components and saturation status."""
        return {
            "p": self.last_p,
            "i": self.last_i,
            "d": self.last_d,
            "unconstrained": self.last_unconstrained,
            "output": self.last_output,
            "is_saturated": self.is_saturated,
            "integral_accumulator": self.integral,
        }
