"""
Unit tests for Mass-Spring-Damper physical model.

Uses Python's built-in `unittest` module so tests run without external dependencies.

Verifies:
- Parameter validation (mass, damping, stiffness).
- Equilibrium formulas and analytical steady-state calculations.
- Overdamped natural frequency and damping ratio.
- Open-loop dynamic convergence to analytical steady-state.
- Energy dissipation in unforced free decay.
- Numerical integration fidelity (RK4 vs. Forward Euler).
- State reset logic.
"""

import unittest
import numpy as np
from src.plant import MassSpringDamper


class TestMassSpringDamper(unittest.TestCase):
    """Test suite verifying physics calculations of the Mass-Spring-Damper system."""

    def test_parameter_validation(self):
        """Ensure invalid physical parameters raise meaningful ValueErrors."""
        # Mass must be strictly positive
        with self.assertRaises(ValueError):
            MassSpringDamper(mass=0.0)
        with self.assertRaises(ValueError):
            MassSpringDamper(mass=-2.0)

        # Damping cannot be negative
        with self.assertRaises(ValueError):
            MassSpringDamper(damping=-1.0)

        # Stiffness cannot be negative
        with self.assertRaises(ValueError):
            MassSpringDamper(stiffness=-5.0)

    def test_analytical_properties(self):
        """Verify natural frequency, damping ratio, and steady-state formulas."""
        plant = MassSpringDamper(mass=1.0, damping=10.0, stiffness=20.0)

        # omega_n = sqrt(k / m) = sqrt(20) = 4.472136...
        expected_wn = np.sqrt(20.0)
        self.assertTrue(np.isclose(plant.natural_frequency, expected_wn, rtol=1e-5))

        # zeta = c / (2 * sqrt(m * k)) = 10 / (2 * sqrt(20)) = 5 / sqrt(20) = 1.118034...
        expected_zeta = 10.0 / (2.0 * np.sqrt(20.0))
        self.assertTrue(np.isclose(plant.damping_ratio, expected_zeta, rtol=1e-5))
        self.assertGreater(plant.damping_ratio, 1.0)  # Must be strictly overdamped

        # Steady-state force to hold at x = 1.0 m: F = k * x = 20 * 1 = 20 N
        self.assertTrue(np.isclose(plant.steady_state_force(1.0), 20.0))
        self.assertTrue(np.isclose(plant.steady_state_force(0.5), 10.0))

        # Steady-state position under constant force: x = F / k
        self.assertTrue(np.isclose(plant.steady_state_position(20.0), 1.0))
        self.assertTrue(np.isclose(plant.steady_state_position(10.0), 0.5))
        self.assertTrue(np.isclose(plant.steady_state_position(0.0), 0.0))

    def test_open_loop_steady_state_convergence(self):
        """
        Apply a constant 20 N force to a system starting at rest (x0=0, v0=0).
        Verify that the system converges smoothly to 1.0 m at t = 4.0 s.
        """
        plant = MassSpringDamper(mass=1.0, damping=10.0, stiffness=20.0)
        dt = 0.005
        steps = int(4.0 / dt)

        for _ in range(steps):
            plant.step(force=20.0, dt=dt, method="rk4")

        # At steady state (t = 4 s > 10 * tau_slow), x is 1.0 m and velocity is ~0 m/s
        self.assertTrue(np.isclose(plant.position, 1.0, atol=1e-3))
        self.assertTrue(np.isclose(plant.velocity, 0.0, atol=1e-3))

    def test_free_decay_energy_dissipation(self):
        """
        Displace mass to x0 = 1.0 m with zero applied force (u = 0).
        Verify that damping dissipates motion and brings the mass back to equilibrium (x = 0).
        """
        plant = MassSpringDamper(mass=1.0, damping=10.0, stiffness=20.0, initial_position=1.0)
        dt = 0.005
        steps = int(4.0 / dt)

        for _ in range(steps):
            plant.step(force=0.0, dt=dt, method="rk4")

        # Should return to rest at x = 0
        self.assertTrue(np.isclose(plant.position, 0.0, atol=1e-3))
        self.assertTrue(np.isclose(plant.velocity, 0.0, atol=1e-3))

    def test_rk4_superior_accuracy_over_euler(self):
        """
        Compare numerical error of RK4 vs. Forward Euler at a moderate time step (dt = 0.05 s)
        against a fine-step reference solution (RK4, dt = 0.0005 s).
        """
        dt_fine = 0.0005
        t_end = 2.0
        steps_fine = int(t_end / dt_fine)

        ref_plant = MassSpringDamper(mass=1.0, damping=10.0, stiffness=20.0)
        for _ in range(steps_fine):
            ref_plant.step(force=20.0, dt=dt_fine, method="rk4")
        true_x = ref_plant.position

        # Run with coarse step dt = 0.05 s
        dt_coarse = 0.05
        steps_coarse = int(t_end / dt_coarse)

        plant_rk4 = MassSpringDamper(mass=1.0, damping=10.0, stiffness=20.0)
        plant_euler = MassSpringDamper(mass=1.0, damping=10.0, stiffness=20.0)

        for _ in range(steps_coarse):
            plant_rk4.step_rk4(force=20.0, dt=dt_coarse)
            plant_euler.step_euler(force=20.0, dt=dt_coarse)

        err_rk4 = abs(plant_rk4.position - true_x)
        err_euler = abs(plant_euler.position - true_x)

        # RK4 error should be strictly smaller than Euler error
        self.assertLess(err_rk4, err_euler)
        self.assertLess(err_rk4, 1e-4)  # High precision even at dt = 0.05 s

    def test_reset_behavior(self):
        """Verify that reset restores state accurately."""
        plant = MassSpringDamper(mass=1.0, damping=10.0, stiffness=20.0)
        plant.step(force=20.0, dt=0.1, method="rk4")

        self.assertNotEqual(plant.position, 0.0)
        plant.reset(initial_position=0.5, initial_velocity=-0.2)
        self.assertEqual(plant.position, 0.5)
        self.assertEqual(plant.velocity, -0.2)


if __name__ == "__main__":
    unittest.main()
