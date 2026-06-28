"""
Wireless Channel Model for the Client-Aware WiFi RRM Simulator.

Models the stochastic and time-varying nature of the wireless channel.
This module consumes the deterministic path loss from the Propagation Model and
applies statistical variations.

Models included:
- Log-normal Shadow Fading (large-scale stochastic fading)
- Rayleigh Fading (small-scale NLOS multipath fading)
- Rician Fading (small-scale LOS multipath fading)
- Doppler Shift (time-selective fading)
- Delay Spread and Coherence Bandwidth (frequency-selective fading)

Sources:
    - Rappaport, "Wireless Communications: Principles and Practice", 2nd Ed.
"""

import math
import random
from typing import Tuple

from src.realistic_simulator.constants import SPEED_OF_LIGHT_MPS


class ChannelModel:
    """Applies stochastic variations to the wireless channel."""

    def __init__(self, enable_shadowing: bool = True, enable_fast_fading: bool = True):
        self.enable_shadowing = enable_shadowing
        self.enable_fast_fading = enable_fast_fading

    def shadow_fading_db(self, std_dev_db: float) -> float:
        """
        Generates log-normal shadow fading.

        Formula:
            Xσ ~ N(0, σ^2)

        Args:
            std_dev_db: Standard deviation of the shadow fading (σ) in dB.

        Returns:
            Shadow fading loss in dB. Can be positive or negative.
        """
        if not self.enable_shadowing or std_dev_db <= 0:
            return 0.0
        return random.gauss(0.0, std_dev_db)

    def rayleigh_fading_db(self) -> float:
        """
        Generates Rayleigh fading for Non-Line-Of-Sight (NLOS) environments.
        The envelope follows a Rayleigh distribution.

        Returns:
            Fading gain in dB (typically negative, representing a deep fade).
        """
        if not self.enable_fast_fading:
            return 0.0
            
        # Rayleigh envelope R = sqrt(X^2 + Y^2) where X, Y ~ N(0, 1)
        # Or more simply, using the inverse transform method: R = sqrt(-2 * ln(U))
        u = random.uniform(1e-9, 1.0)
        envelope = math.sqrt(-2.0 * math.log(u))
        
        # Convert envelope to power gain (linear) and then to dB
        # R^2 is exponentially distributed with mean 2. We normalize to mean power 1.
        power_linear = (envelope ** 2) / 2.0
        return 10.0 * math.log10(power_linear)

    def rician_fading_db(self, k_factor_db: float) -> float:
        """
        Generates Rician fading for Line-Of-Sight (LOS) environments.
        When K = 0 (linear), it converges to Rayleigh.

        Args:
            k_factor_db: The ratio of signal power in dominant component over the 
                         (local-mean) scattered power in dB.

        Returns:
            Fading gain in dB.
        """
        if not self.enable_fast_fading:
            return 0.0

        k_linear = 10.0 ** (k_factor_db / 10.0)
        
        # Mean of dominant component
        mu = math.sqrt(k_linear / (k_linear + 1))
        # Variance of scattered component
        sigma = math.sqrt(1.0 / (2.0 * (k_linear + 1)))

        # Complex Gaussian with non-zero mean
        x = random.gauss(mu, sigma)
        y = random.gauss(0.0, sigma)

        envelope = math.sqrt(x**2 + y**2)
        power_linear = envelope ** 2
        return 10.0 * math.log10(max(1e-9, power_linear))

    def doppler_shift_hz(self, velocity_mps: float, freq_hz: float) -> float:
        """
        Computes the maximum Doppler shift based on relative velocity.

        Formula:
            fD = (v * f) / c

        Args:
            velocity_mps: Relative velocity between transmitter and receiver in m/s.
            freq_hz: Carrier frequency in Hertz.

        Returns:
            Maximum Doppler shift in Hz.
        """
        return (velocity_mps * freq_hz) / SPEED_OF_LIGHT_MPS

    def coherence_time_s(self, doppler_shift_hz: float) -> float:
        """
        Computes the coherence time of the channel.

        Formula:
            Tc ≈ 0.423 / fD

        Args:
            doppler_shift_hz: Maximum Doppler shift in Hz.

        Returns:
            Coherence time in seconds.
        """
        if doppler_shift_hz <= 0:
            return float('inf')
        return 0.423 / doppler_shift_hz

    def coherence_bandwidth_hz(self, rms_delay_spread_s: float) -> float:
        """
        Computes the coherence bandwidth of the channel.

        Formula:
            Bc ≈ 1 / (5 * τ_rms)

        Args:
            rms_delay_spread_s: RMS delay spread in seconds.

        Returns:
            Coherence bandwidth in Hz.
        """
        if rms_delay_spread_s <= 0:
            return float('inf')
        return 1.0 / (5.0 * rms_delay_spread_s)

    def apply_channel_effects(self, total_path_loss_db: float, is_los: bool,
                              shadow_std_dev_db: float, k_factor_db: float = 6.0) -> Tuple[float, float, float]:
        """
        Applies all channel fading effects to the deterministic path loss.

        Args:
            total_path_loss_db: Deterministic path loss from Propagation Engine.
            is_los: Whether a direct Line-Of-Sight exists (no walls).
            shadow_std_dev_db: Shadow fading standard deviation.
            k_factor_db: Rician K-factor (used if LOS).

        Returns:
            Tuple containing:
                - Total channel loss in dB (path_loss + shadow_loss - fast_fading_gain)
                - Shadow loss component in dB
                - Fast fading gain component in dB
        """
        shadow_loss_db = self.shadow_fading_db(shadow_std_dev_db)
        
        if is_los:
            fast_fading_gain_db = self.rician_fading_db(k_factor_db)
        else:
            fast_fading_gain_db = self.rayleigh_fading_db()

        # Total Loss = Path Loss + Shadowing - Fading Gain
        total_loss_db = total_path_loss_db + shadow_loss_db - fast_fading_gain_db
        return total_loss_db, shadow_loss_db, fast_fading_gain_db
