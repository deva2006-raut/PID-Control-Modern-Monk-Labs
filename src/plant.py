"""
Plant Dynamics: Second-Order Mass-Spring-Damper Physical System.

This module models the continuous-time physics of a 1D mechanical system
governed by Newton's Second Law:
    m * x_ddot(t) + c * x_dot(t) + k * x(t) = u(t)

Where:
    m : Mass (kg)
    c : Viscous damping coefficient (N*s/m)
    k : Spring stiffness constant (N/m)
    x : Position of mass from equilibrium (m)
    x_dot : Velocity of mass (m/s)
    x_ddot: Acceleration of mass (m/s^2)
    u : External control force applied to mass (N)

Supported numerical integration schemes:
    - Forward Euler (1st order approximation, fast, sensitive to step size)
    - Runge-Kutta 4th Order (RK4: 4th order approximation, high fidelity)
"""

from typing import Tuple, Dict
import numpy as np


class MassSpringDamper:
    """
    Simulation model for a 1-DOF (Degree of Freedom) Mass-Spring-Damper system.

    Parameters
    ----------
    mass : float, default=1.0
        Mass of the body in kilograms [kg]. Must be strictly positive.
    damping : float, default=10.0
        Viscous friction/damping coefficient [N*s/m]. Opposes velocity.
    stiffness : float, default=20.0
        Spring stiffness constant [N/m]. Pulls mass toward position x = 0.
    initial_position : float, default=0.0
        Initial displacement from equilibrium [m].
    initial_velocity : float, default=0.0
        Initial velocity [m/s].
    """

    def __init__(
        self,
        mass: float = 1.0,
        damping: float = 10.0,
        stiffness: float = 20.0,
        initial_position: float = 0.0,
        initial_velocity: float = 0.0,
    ) -> None:
        if mass <= 0.0:
            raise ValueError(f"Mass must be strictly positive (> 0), got {mass} kg.")
        if damping < 0.0:
            raise ValueError(f"Damping coefficient cannot be negative, got {damping} N*s/m.")
        if stiffness < 0.0:
            raise ValueError(f"Spring stiffness cannot be negative, got {stiffness} N/m.")

        self.m: float = float(mass)
        self.c: float = float(damping)
        self.k: float = float(stiffness)

        # Internal state vector: [position x (m), velocity v (m/s)]
        self.x: float = float(initial_position)
        self.v: float = float(initial_velocity)

    @property
    def position(self) -> float:
        """Current displacement x from equilibrium in metres [m]."""
        return self.x

    @property
    def velocity(self) -> float:
        """Current velocity v = dx/dt in metres per second [m/s]."""
        return self.v

    @property
    def state(self) -> Tuple[float, float]:
        """Current state tuple (position, velocity) in [m, m/s]."""
        return self.x, self.v

    @property
    def natural_frequency(self) -> float:
        """
        Undamped natural frequency: omega_n = sqrt(k / m) in radians/second [rad/s].
        Represents how fast the system would oscillate if there were zero damping.
        """
        return np.sqrt(self.k / self.m)

    @property
    def damping_ratio(self) -> float:
        """
        Dimensionless damping ratio: zeta = c / (2 * sqrt(m * k)).
        - zeta < 1: Underdamped (oscillates before settling)
        - zeta = 1: Critically damped (fastest settling without overshoot)
        - zeta > 1: Overdamped (sluggish, purely exponential decay, no oscillation)
        """
        return self.c / (2.0 * np.sqrt(self.m * self.k))

    def reset(self, initial_position: float = 0.0, initial_velocity: float = 0.0) -> None:
        """
        Reset the system state to specified initial conditions.

        Parameters
        ----------
        initial_position : float
            Position to reset to [m].
        initial_velocity : float
            Velocity to reset to [m/s].
        """
        self.x = float(initial_position)
        self.v = float(initial_velocity)

    def compute_acceleration(self, position: float, velocity: float, force: float) -> float:
        """
        Compute instantaneous acceleration from Newton's Second Law:
            F_net = m * a
            u - c * v - k * x = m * a
            a = (u - c * v - k * x) / m

        Parameters
        ----------
        position : float
            Displacement x [m].
        velocity : float
            Velocity v [m/s].
        force : float
            Applied external actuator force u [N].

        Returns
        -------
        acceleration : float
            Instantaneous acceleration d^2x/dt^2 [m/s^2].
        """
        # Net force = Applied Force - Damper Force - Spring Force
        f_net = force - (self.c * velocity) - (self.k * position)
        return f_net / self.m

    def step_euler(self, force: float, dt: float) -> Tuple[float, float]:
        """
        Advance the simulation by time dt using the Forward Euler method.

        Equations:
            x[k+1] = x[k] + v[k] * dt
            v[k+1] = v[k] + a[k] * dt
        where a[k] = (u[k] - c*v[k] - k*x[k]) / m

        Parameters
        ----------
        force : float
            Control input force u [N] held constant over interval dt.
        dt : float
            Discrete simulation time step [s]. Must be strictly positive.

        Returns
        -------
        (position, velocity) : Tuple[float, float]
            Updated system state after interval dt.
        """
        if dt <= 0.0:
            raise ValueError(f"Time step dt must be positive (> 0), got {dt} s.")

        a = self.compute_acceleration(self.x, self.v, force)
        self.x += self.v * dt
        self.v += a * dt
        return self.x, self.v

    def step_rk4(self, force: float, dt: float) -> Tuple[float, float]:
        """
        Advance the simulation by time dt using the classical Runge-Kutta 4th Order (RK4).

        RK4 evaluates derivatives at 4 points across the step [t, t+dt] to achieve
        O(dt^4) local error accuracy, providing superior numerical stability.

        Parameters
        ----------
        force : float
            Control input force u [N] held constant over interval dt.
        dt : float
            Discrete simulation time step [s].

        Returns
        -------
        (position, velocity) : Tuple[float, float]
            Updated system state after interval dt.
        """
        if dt <= 0.0:
            raise ValueError(f"Time step dt must be positive (> 0), got {dt} s.")

        x0, v0 = self.x, self.v

        # k1: Slope at beginning of interval
        k1_x = v0
        k1_v = self.compute_acceleration(x0, v0, force)

        # k2: Slope at midpoint using k1
        x_mid1 = x0 + 0.5 * dt * k1_x
        v_mid1 = v0 + 0.5 * dt * k1_v
        k2_x = v_mid1
        k2_v = self.compute_acceleration(x_mid1, v_mid1, force)

        # k3: Slope at midpoint using k2
        x_mid2 = x0 + 0.5 * dt * k2_x
        v_mid2 = v0 + 0.5 * dt * k2_v
        k3_x = v_mid2
        k3_v = self.compute_acceleration(x_mid2, v_mid2, force)

        # k4: Slope at end of interval using k3
        x_end = x0 + dt * k3_x
        v_end = v0 + dt * k3_v
        k4_x = v_end
        k4_v = self.compute_acceleration(x_end, v_end, force)

        # Weighted average update
        self.x += (dt / 6.0) * (k1_x + 2.0 * k2_x + 2.0 * k3_x + k4_x)
        self.v += (dt / 6.0) * (k1_v + 2.0 * k2_v + 2.0 * k3_v + k4_v)

        return self.x, self.v

    def step(self, force: float, dt: float, method: str = "rk4") -> Tuple[float, float]:
        """
        Convenience dispatcher to advance the system by one time step.

        Parameters
        ----------
        force : float
            Applied control input force u [N].
        dt : float
            Time step [s].
        method : str, default="rk4"
            Numerical scheme: 'rk4' or 'euler'.
        """
        scheme = method.strip().lower()
        if scheme == "rk4":
            return self.step_rk4(force, dt)
        elif scheme in ("euler", "forward_euler"):
            return self.step_euler(force, dt)
        else:
            raise ValueError(f"Unknown integration method: '{method}'. Choose 'rk4' or 'euler'.")

    def steady_state_force(self, target_position: float) -> float:
        """
        Calculate analytical force required to maintain equilibrium at target position.
        At steady state: acceleration = 0, velocity = 0.
        Newton's law yields: u_ss = k * x_target.
        """
        return self.k * float(target_position)

    def steady_state_position(self, applied_force: float) -> float:
        """
        Calculate analytical displacement at equilibrium for a constant applied force.
        At steady state: x_ss = u / k.
        """
        return float(applied_force) / self.k

    def to_dict(self) -> Dict[str, float]:
        """Export parameters and state as a dictionary for logging and inspection."""
        return {
            "mass_kg": self.m,
            "damping_Ns_per_m": self.c,
            "stiffness_N_per_m": self.k,
            "position_m": self.x,
            "velocity_mps": self.v,
            "omega_n_rad_per_s": self.natural_frequency,
            "damping_ratio_zeta": self.damping_ratio,
        }
