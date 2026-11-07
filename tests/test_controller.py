"""
Unit tests for the modular PID Controller.

Uses Python's built-in `unittest` module.

Verifies:
- Parameter validation (gains, limits, filter constant, time step).
- Isolated Proportional (P), Integral (I), and Derivative (D) responses.
- Output saturation clamping within [-30 N, +30 N].
- Anti-windup conditional integration vs. naive integrator windup.
- Derivative kick prevention (derivative-on-measurement).
- First-order derivative low-pass filter attenuation.
- State reset behavior.
"""

import unittest
import numpy as np
from src.controller import PIDController


class TestPIDController(unittest.TestCase):
    """Test suite verifying controller logic, safety guardrails, and numerical fidelity."""

    def test_parameter_validation(self):
        """Ensure invalid gains, limits, or parameters raise ValueErrors."""
        # Negative gains rejected
        with self.assertRaises(ValueError):
            PIDController(kp=-1.0)
        with self.assertRaises(ValueError):
            PIDController(ki=-0.5)
        with self.assertRaises(ValueError):
            PIDController(kd=-2.0)

        # Invalid saturation limits (min >= max)
        with self.assertRaises(ValueError):
            PIDController(output_limits=(30.0, -30.0))
        with self.assertRaises(ValueError):
            PIDController(output_limits=(10.0, 10.0))

        # Negative filter tau
        with self.assertRaises(ValueError):
            PIDController(filter_tau=-0.1)

        # Invalid time step dt <= 0 in update
        pid = PIDController(kp=1.0)
        with self.assertRaises(ValueError):
            pid.update(setpoint=1.0, measurement=0.0, dt=0.0)
        with self.assertRaises(ValueError):
            pid.update(setpoint=1.0, measurement=0.0, dt=-0.01)

    def test_proportional_action_isolated(self):
        """Verify pure P-controller output equals Kp * error."""
        pid = PIDController(kp=15.0, ki=0.0, kd=0.0, output_limits=(-100.0, 100.0))

        # Test positive error: setpoint = 1.0 m, measurement = 0.2 m => error = 0.8 m
        # Expected u = 15.0 * 0.8 = 12.0 N
        u = pid.update(setpoint=1.0, measurement=0.2, dt=0.01)
        self.assertAlmostEqual(u, 12.0, places=5)
        self.assertAlmostEqual(pid.last_p, 12.0, places=5)
        self.assertEqual(pid.last_i, 0.0)
        self.assertEqual(pid.last_d, 0.0)

        # Test negative error: setpoint = 0.0 m, measurement = 0.5 m => error = -0.5 m
        # Expected u = 15.0 * (-0.5) = -7.5 N
        u_neg = pid.update(setpoint=0.0, measurement=0.5, dt=0.01)
        self.assertAlmostEqual(u_neg, -7.5, places=5)

    def test_integral_action_isolated(self):
        """Verify pure I-controller accumulates error over time according to Ki * error * dt."""
        pid = PIDController(kp=0.0, ki=5.0, kd=0.0, output_limits=(-100.0, 100.0))
        dt = 0.1

        # Step 1: error = 1.0 m, delta_I = 5.0 * 1.0 * 0.1 = 0.5 N
        u1 = pid.update(setpoint=1.0, measurement=0.0, dt=dt)
        self.assertAlmostEqual(u1, 0.5, places=5)
        self.assertAlmostEqual(pid.integral, 0.5, places=5)

        # Step 2: error = 1.0 m, cumulative_I = 0.5 + 0.5 = 1.0 N
        u2 = pid.update(setpoint=1.0, measurement=0.0, dt=dt)
        self.assertAlmostEqual(u2, 1.0, places=5)
        self.assertAlmostEqual(pid.integral, 1.0, places=5)

        # Step 3: zero error => integral should hold constant at 1.0 N
        u3 = pid.update(setpoint=1.0, measurement=1.0, dt=dt)
        self.assertAlmostEqual(u3, 1.0, places=5)
        self.assertAlmostEqual(pid.integral, 1.0, places=5)

    def test_derivative_on_measurement_eliminates_kick(self):
        """
        Verify that a sudden step change in the setpoint DOES NOT cause a derivative spike
        when derivative_on_measurement is enabled.
        """
        # Controller with derivative on measurement
        pid_kick_free = PIDController(
            kp=0.0, ki=0.0, kd=10.0,
            derivative_on_measurement=True,
            output_limits=(-100.0, 100.0)
        )

        # Step 1: Initial state at rest (setpoint = 0.0, measurement = 0.0)
        pid_kick_free.update(setpoint=0.0, measurement=0.0, dt=0.01)

        # Step 2: Setpoint suddenly jumps to 10.0 m, but measurement stays at 0.0 m
        u_kick_free = pid_kick_free.update(setpoint=10.0, measurement=0.0, dt=0.01)

        # Since measurement did not move (dy = 0), derivative must be zero! No kick!
        self.assertEqual(pid_kick_free.last_d, 0.0)
        self.assertEqual(u_kick_free, 0.0)

        # Controller with derivative on error (traditional naive PID)
        pid_naive = PIDController(
            kp=0.0, ki=0.0, kd=10.0,
            derivative_on_measurement=False,
            output_limits=(-20000.0, 20000.0)
        )
        pid_naive.update(setpoint=0.0, measurement=0.0, dt=0.01)
        # Jumps to 10.0 m => delta_e = 10.0 m => de/dt = 10 / 0.01 = 1000 m/s => D = 10000 N!
        u_naive = pid_naive.update(setpoint=10.0, measurement=0.0, dt=0.01)
        self.assertGreater(u_naive, 5000.0)  # Huge derivative kick
        self.assertAlmostEqual(pid_naive.last_d, 10000.0, places=3)

    def test_derivative_action_on_moving_measurement(self):
        """Verify derivative resists velocity: D = -Kd * (dy/dt)."""
        pid = PIDController(
            kp=0.0, ki=0.0, kd=4.0,
            derivative_on_measurement=True,
            filter_tau=0.0,
            output_limits=(-100.0, 100.0)
        )
        # Step 1: start at measurement = 0.0
        pid.update(setpoint=1.0, measurement=0.0, dt=0.1)

        # Step 2: measurement moves to 0.2 m in dt = 0.1 s => dy/dt = 2.0 m/s
        # Expected D = -4.0 * 2.0 = -8.0 N (braking force opposing motion)
        u = pid.update(setpoint=1.0, measurement=0.2, dt=0.1)
        self.assertAlmostEqual(u, -8.0, places=5)
        self.assertAlmostEqual(pid.last_d, -8.0, places=5)

    def test_derivative_low_pass_filter(self):
        """Verify that derivative filter attenuates high-frequency noise."""
        dt = 0.005
        tau = 0.05  # Filter time constant = 50 ms

        pid_unfiltered = PIDController(kp=0.0, ki=0.0, kd=1.0, filter_tau=0.0, output_limits=(-100, 100))
        pid_filtered = PIDController(kp=0.0, ki=0.0, kd=1.0, filter_tau=tau, output_limits=(-100, 100))

        # Initial baseline step
        pid_unfiltered.update(setpoint=1.0, measurement=0.0, dt=dt)
        pid_filtered.update(setpoint=1.0, measurement=0.0, dt=dt)

        # Simulate noisy sensor alternating: +0.001 m, -0.001 m (1 mm noise)
        noisy_measurements = [0.001, -0.001, 0.001, -0.001, 0.001]
        unfiltered_d_vals = []
        filtered_d_vals = []

        for y in noisy_measurements:
            pid_unfiltered.update(setpoint=1.0, measurement=y, dt=dt)
            pid_filtered.update(setpoint=1.0, measurement=y, dt=dt)
            unfiltered_d_vals.append(abs(pid_unfiltered.last_d))
            filtered_d_vals.append(abs(pid_filtered.last_d))

        # The filtered derivative magnitude should be substantially lower than unfiltered
        self.assertLess(np.mean(filtered_d_vals), np.mean(unfiltered_d_vals))

    def test_output_saturation_bounds(self):
        """Verify controller output is strictly clamped within [-30 N, +30 N]."""
        pid = PIDController(kp=100.0, output_limits=(-30.0, 30.0))

        # High positive error: 100 * 5.0 = 500 N => clamped to +30 N
        u_pos = pid.update(setpoint=5.0, measurement=0.0, dt=0.01)
        self.assertEqual(u_pos, 30.0)
        self.assertTrue(pid.is_saturated)

        # High negative error: 100 * (-5.0) = -500 N => clamped to -30 N
        u_neg = pid.update(setpoint=-5.0, measurement=0.0, dt=0.01)
        self.assertEqual(u_neg, -30.0)
        self.assertTrue(pid.is_saturated)

    def test_anti_windup_clamping(self):
        """
        Verify anti-windup clamping prevents integral term from blowing up during saturation,
        allowing immediate recovery when error reverses sign.
        """
        # Controller A: With Anti-Windup Clamping
        pid_antiwindup = PIDController(
            kp=10.0, ki=50.0, kd=0.0,
            output_limits=(-30.0, 30.0),
            anti_windup=True
        )

        # Controller B: Without Anti-Windup (Naive Windup)
        pid_naive = PIDController(
            kp=10.0, ki=50.0, kd=0.0,
            output_limits=(-30.0, 30.0),
            anti_windup=False
        )

        dt = 0.05
        # Saturate both controllers for 100 steps (5 seconds) with error = 1.0 m
        for _ in range(100):
            pid_antiwindup.update(setpoint=1.0, measurement=0.0, dt=dt)
            pid_naive.update(setpoint=1.0, measurement=0.0, dt=dt)

        # The anti-windup controller keeps its integral clamped at actuator limit (30 N)
        self.assertLessEqual(pid_antiwindup.integral, 30.0)

        # The naive controller winds up to 50 * 1.0 * 5.0 = 250 N!
        self.assertGreater(pid_naive.integral, 200.0)

        # Now reverse error: system overshoots (measurement = 2.0 m, error = -1.0 m)
        u_aw = pid_antiwindup.update(setpoint=1.0, measurement=2.0, dt=dt)
        u_naive = pid_naive.update(setpoint=1.0, measurement=2.0, dt=dt)

        # Anti-windup controller responds immediately with negative or reduced force
        # P = 10 * (-1.0) = -10 N. Saturated force drops right away.
        self.assertLess(u_aw, 30.0)

        # Naive controller is still stuck at +30.0 N because integral is huge (~250 N)!
        self.assertEqual(u_naive, 30.0)

    def test_reset_functionality(self):
        """Verify reset clears integrator, memory, and diagnostics."""
        pid = PIDController(kp=10.0, ki=5.0, kd=2.0)
        pid.update(setpoint=1.0, measurement=0.0, dt=0.01)

        self.assertNotEqual(pid.integral, 0.0)
        self.assertIsNotNone(pid.prev_error)

        pid.reset()
        self.assertEqual(pid.integral, 0.0)
        self.assertIsNone(pid.prev_error)
        self.assertIsNone(pid.prev_measurement)
        self.assertEqual(pid.filtered_derivative, 0.0)
        self.assertEqual(pid.last_output, 0.0)
        self.assertFalse(pid.is_saturated)


if __name__ == "__main__":
    unittest.main()
