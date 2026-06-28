"""
Physical Propagation Model for the Client-Aware WiFi RRM Simulator.

Computes deterministic signal attenuation over distance based on the physical
environment. This module represents the large-scale path loss component of the
wireless channel.

Models included:
- Friis Free Space Path Loss (used for the near-field d0 reference)
- Log-Distance Path Loss (distance-based decay)
- Wall/Obstruction Attenuation (sum of intersected material losses)

Sources:
    - Rappaport, "Wireless Communications: Principles and Practice", 2nd Ed.
"""

import math
from typing import List

from src.realistic_simulator.constants import SPEED_OF_LIGHT_MPS
from src.realistic_simulator.environment import WirelessEnvironment, Point


class PropagationEngine:
    """Computes deterministic signal attenuation based on the environment."""

    def __init__(self, environment: WirelessEnvironment):
        self.env = environment

    def free_space_path_loss(self, distance_m: float, freq_hz: float) -> float:
        """
        Computes the Free Space Path Loss (FSPL) using the Friis transmission equation.
        Usually used to compute the reference loss at d0 = 1 meter.

        Formula:
            FSPL(dB) = 20 * log10(d) + 20 * log10(f) - 147.55
            (Derived from: (4πdf / c)^2)

        Args:
            distance_m: Distance in meters (must be > 0).
            freq_hz: Frequency in Hertz.

        Returns:
            Path loss in dB.
        """
        if distance_m <= 0:
            return 0.0
        
        # 147.55 is 20*log10(4π/c) in dB
        # 20 * log10(4 * PI / 299792458) = -147.552
        constant = 20 * math.log10(4 * math.pi / SPEED_OF_LIGHT_MPS)
        fspl = 20 * math.log10(distance_m) + 20 * math.log10(freq_hz) + constant
        return fspl

    def log_distance_path_loss(self, distance_m: float, freq_hz: float,
                               path_loss_exponent: float, reference_distance_m: float = 1.0) -> float:
        """
        Computes the median Log-Distance Path Loss.
        Note: Shadow fading (Xσ) is NOT included here; it is applied in the Channel Model.

        Formula:
            PL(d) = PL(d0) + 10 * n * log10(d / d0)

        Args:
            distance_m: Distance in meters.
            freq_hz: Frequency in Hertz.
            path_loss_exponent: Path loss exponent (n).
            reference_distance_m: Reference distance d0 (typically 1.0 m indoors).

        Returns:
            Path loss in dB.
        """
        if distance_m <= reference_distance_m:
            return self.free_space_path_loss(distance_m, freq_hz)

        pl_d0 = self.free_space_path_loss(reference_distance_m, freq_hz)
        pl_d = pl_d0 + 10 * path_loss_exponent * math.log10(distance_m / reference_distance_m)
        return pl_d

    def total_path_loss(self, point_a: Point, point_b: Point, freq_hz: float,
                        path_loss_exponent: float, reference_distance_m: float = 1.0) -> float:
        """
        Computes the total deterministic path loss between two points, including
        log-distance loss and wall attenuation.

        Args:
            point_a: Start point.
            point_b: End point.
            freq_hz: Frequency in Hertz.
            path_loss_exponent: Path loss exponent (n).
            reference_distance_m: Reference distance d0.

        Returns:
            Total path loss in dB.
        """
        distance = point_a.distance_to(point_b)
        
        # Log-distance path loss
        pl_distance = self.log_distance_path_loss(
            distance, freq_hz, path_loss_exponent, reference_distance_m
        )
        
        # Wall/Obstacle attenuation
        pl_walls = self.env.total_wall_attenuation(point_a, point_b)
        
        return pl_distance + pl_walls
