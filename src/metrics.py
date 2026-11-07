"""
Control Systems Performance Metrics: Time-Domain Step-Response Evaluation.

This module provides standard control engineering performance metric calculators:
1. Rise Time (t_r): Time required for the response to rise from 10% to 90% of the target setpoint.
2. Percentage Overshoot (M_p): Maximum percentage by which the response exceeds the target setpoint.
3. Settling Time (t_s): Time after which the response enters and remains within a specified
   tolerance band (standard: 2% band: [0.98 * target, 1.02 * target]).
4. Steady-State Error (e_ss): Magnitude of remaining deviation |target - y_final| after transient
   behavior has decayed.

All functions handle non-converging or heavily offset responses safely by returning None / NaN
with informative status reporting.
"""

from typing import Optional, Dict, Any
import numpy as np


def calculate_rise_time(
    time: np.ndarray,
    response: np.ndarray,
    target: float = 1.0,
    lower_threshold: float = 0.1,
    upper_threshold: float = 0.9,
) -> Optional[float]:
    """
    Calculate 10% to 90% Rise Time (t_r) relative to the target setpoint.

    Parameters
    ----------
    time : np.ndarray
        Array of simulation time points [s].
    response : np.ndarray
        Array of system positions [m].
    target : float, default=1.0
        Target setpoint value [m].
    lower_threshold : float, default=0.1
        Fraction of target representing lower threshold (10%).
    upper_threshold : float, default=0.9
        Fraction of target representing upper threshold (90%).

    Returns
    -------
    rise_time : Optional[float]
        t_90 - t_10 in seconds [s], or None if response fails to reach 90% of target.
    """
    if len(time) != len(response):
        raise ValueError("time and response arrays must have identical length.")
    if target == 0.0:
        raise ValueError("Target setpoint cannot be zero for relative rise time calculation.")

    y_low = lower_threshold * target
    y_high = upper_threshold * target

    idx_low = np.where(response >= y_low)[0]
    idx_high = np.where(response >= y_high)[0]

    # If the signal never reaches the thresholds, rise time is undefined
    if len(idx_low) == 0 or len(idx_high) == 0:
        return None

    t_10 = time[idx_low[0]]
    t_90 = time[idx_high[0]]

    # Ensure valid forward time difference
    if t_90 < t_10:
        return None

    return float(t_90 - t_10)


def calculate_overshoot(
    response: np.ndarray,
    target: float = 1.0,
) -> float:
    """
    Calculate Percentage Overshoot (M_p).

    Formula:
        M_p = max(0, (max(y) - target) / target * 100%)

    Parameters
    ----------
    response : np.ndarray
        Array of system positions [m].
    target : float, default=1.0
        Target setpoint value [m].

    Returns
    -------
    overshoot_percent : float
        Percentage overshoot [%]. Returns 0.0 if response never exceeds target.
    """
    if target == 0.0:
        raise ValueError("Target setpoint cannot be zero for percentage overshoot.")

    peak_value = np.max(response)
    if peak_value <= target:
        return 0.0

    return float((peak_value - target) / abs(target) * 100.0)


def calculate_settling_time(
    time: np.ndarray,
    response: np.ndarray,
    target: float = 1.0,
    tolerance: float = 0.02,
) -> Optional[float]:
    """
    Calculate 2% Settling Time (t_s).

    Settling time is the earliest time point after which the response enters
    and PERMANENTLY stays within the tolerance band:
        [target * (1 - tolerance), target * (1 + tolerance)]

    Parameters
    ----------
    time : np.ndarray
        Array of simulation time points [s].
    response : np.ndarray
        Array of system positions [m].
    target : float, default=1.0
        Target setpoint value [m].
    tolerance : float, default=0.02
        Error tolerance fraction (0.02 = 2%).

    Returns
    -------
    settling_time : Optional[float]
        Settling time in seconds [s], or None if response does not settle within band.
    """
    if len(time) != len(response):
        raise ValueError("time and response arrays must have identical length.")

    band_half_width = abs(target * tolerance)
    lower_bound = target - band_half_width
    upper_bound = target + band_half_width

    # Find all indices where response is OUTSIDE the tolerance band
    outside_indices = np.where((response < lower_bound) | (response > upper_bound))[0]

    # If response is never outside the band, it started settled at t=0
    if len(outside_indices) == 0:
        return float(time[0])

    last_outside_idx = outside_indices[-1]

    # If the signal is outside at the very end of simulation, it never settled
    if last_outside_idx >= len(time) - 1:
        return None

    # Settling time is the time of the first point that stays within the band thereafter
    settled_idx = last_outside_idx + 1
    return float(time[settled_idx])


def calculate_steady_state_error(
    response: np.ndarray,
    target: float = 1.0,
    window_fraction: float = 0.05,
) -> float:
    """
    Calculate Steady-State Error (e_ss).

    Averages the last window_fraction of samples to suppress numerical jitter.
    Formula:
        e_ss = |target - mean(response[-N:])|

    Parameters
    ----------
    response : np.ndarray
        Array of system positions [m].
    target : float, default=1.0
        Target setpoint value [m].
    window_fraction : float, default=0.05
        Fraction of final samples to average (default 5%).

    Returns
    -------
    steady_state_error : float
        Absolute deviation in metres [m].
    """
    n_samples = len(response)
    window_size = max(1, int(n_samples * window_fraction))
    y_final = np.mean(response[-window_size:])
    return float(abs(target - y_final))


def calculate_performance_metrics(
    time: np.ndarray,
    response: np.ndarray,
    target: float = 1.0,
    tolerance: float = 0.02,
) -> Dict[str, Any]:
    """
    Calculate all standard step-response performance metrics.

    Returns
    -------
    metrics : Dict[str, Any]
        Dictionary containing rise_time_s, overshoot_pct, settling_time_s,
        steady_state_error_m, and final_value_m.
    """
    t_r = calculate_rise_time(time, response, target)
    m_p = calculate_overshoot(response, target)
    t_s = calculate_settling_time(time, response, target, tolerance)
    e_ss = calculate_steady_state_error(response, target)

    n_samples = len(response)
    final_val = float(np.mean(response[-max(1, int(n_samples * 0.05)):]))

    return {
        "rise_time_s": t_r,
        "overshoot_pct": m_p,
        "settling_time_s": t_s,
        "steady_state_error_m": e_ss,
        "final_value_m": final_val,
    }
