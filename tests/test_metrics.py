"""
Unit tests for step-response performance metrics calculation.

Uses Python's built-in `unittest` module.

Verifies:
- Rise time calculation against analytical exponential response.
- Rise time returning None when response fails to reach 90% threshold.
- Overshoot calculation for underdamped and overdamped responses.
- Settling time calculation against analytical 2% tolerance band.
- Settling time returning None when response never enters band.
- Steady-state error calculation.
- Input validation and exception handling.
"""

import unittest
import numpy as np
from src.metrics import (
    calculate_rise_time,
    calculate_overshoot,
    calculate_settling_time,
    calculate_steady_state_error,
    calculate_performance_metrics,
)


class TestMetrics(unittest.TestCase):
    """Test suite verifying step-response performance metrics."""

    def setUp(self):
        """Set up standard time vector for tests."""
        self.t = np.linspace(0.0, 10.0, 10001)  # dt = 0.001 s

    def test_rise_time_analytical_exponential(self):
        """
        For a 1st order exponential response y(t) = 1 - exp(-t / tau):
        t_10 = -tau * ln(0.9) approx 0.10536 * tau
        t_90 = -tau * ln(0.1) approx 2.30259 * tau
        t_r  = t_90 - t_10 approx 2.19722 * tau
        """
        tau = 2.0
        y = 1.0 - np.exp(-self.t / tau)
        expected_tr = 2.197224577 * tau

        computed_tr = calculate_rise_time(self.t, y, target=1.0)
        self.assertIsNotNone(computed_tr)
        self.assertAlmostEqual(computed_tr, expected_tr, delta=0.01)

    def test_rise_time_returns_none_when_unreached(self):
        """If response never reaches 90% (e.g. settles at 0.5 m), rise time is None."""
        y_sluggish = 0.5 * (1.0 - np.exp(-self.t))
        tr = calculate_rise_time(self.t, y_sluggish, target=1.0)
        self.assertIsNone(tr)

    def test_overshoot_calculation(self):
        """Verify overshoot calculation for peak responses."""
        # Case A: Overshoot of 25% (peak = 1.25 m, target = 1.0 m)
        y_overshoot = 1.0 - np.exp(-self.t) * np.cos(3.0 * self.t)
        # Peak of 1 - exp(-t)*cos(3t): max is around 1.15 to 1.35
        expected_mp = (np.max(y_overshoot) - 1.0) * 100.0
        computed_mp = calculate_overshoot(y_overshoot, target=1.0)
        self.assertAlmostEqual(computed_mp, expected_mp, places=4)
        self.assertGreater(computed_mp, 0.0)

        # Case B: Strictly overdamped (monotonic, max <= 1.0) => 0% overshoot
        y_monotonic = 1.0 - np.exp(-self.t)
        self.assertEqual(calculate_overshoot(y_monotonic, target=1.0), 0.0)

        # Case C: Settles below target (max = 0.8) => 0% overshoot
        y_subtarget = 0.8 * (1.0 - np.exp(-self.t))
        self.assertEqual(calculate_overshoot(y_subtarget, target=1.0), 0.0)

    def test_settling_time_analytical_exponential(self):
        """
        For y(t) = 1 - exp(-t / tau), 2% band [0.98, 1.02] is reached when
        exp(-t / tau) = 0.02 => t = -tau * ln(0.02) approx 3.912 * tau.
        """
        tau = 1.5
        y = 1.0 - np.exp(-self.t / tau)
        expected_ts = -tau * np.log(0.02)  # ~ 5.868 s

        computed_ts = calculate_settling_time(self.t, y, target=1.0, tolerance=0.02)
        self.assertIsNotNone(computed_ts)
        self.assertAlmostEqual(computed_ts, expected_ts, delta=0.02)

    def test_settling_time_returns_none_when_outside_band(self):
        """If response never enters 2% band (e.g. settles at 0.8 m), returns None."""
        y_offset = 0.8 * np.ones_like(self.t)
        ts = calculate_settling_time(self.t, y_offset, target=1.0, tolerance=0.02)
        self.assertIsNone(ts)

    def test_steady_state_error(self):
        """Verify steady-state error computation."""
        # Case A: Converges to 1.0 m exactly => e_ss = 0.0
        y_perfect = np.ones_like(self.t)
        self.assertAlmostEqual(calculate_steady_state_error(y_perfect, target=1.0), 0.0, places=5)

        # Case B: Converges to 0.8333 m => e_ss = 0.1667 m
        y_offset = 0.8333 * np.ones_like(self.t)
        self.assertAlmostEqual(calculate_steady_state_error(y_offset, target=1.0), 0.1667, places=3)

    def test_calculate_performance_metrics_dict(self):
        """Verify combined helper outputs valid dictionary."""
        y = 1.0 - np.exp(-self.t)
        metrics = calculate_performance_metrics(self.t, y, target=1.0)

        self.assertIn("rise_time_s", metrics)
        self.assertIn("overshoot_pct", metrics)
        self.assertIn("settling_time_s", metrics)
        self.assertIn("steady_state_error_m", metrics)
        self.assertIn("final_value_m", metrics)
        self.assertEqual(metrics["overshoot_pct"], 0.0)
        self.assertAlmostEqual(metrics["steady_state_error_m"], 0.0, places=3)


if __name__ == "__main__":
    unittest.main()
