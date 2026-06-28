"""
Receiver Model for the Client-Aware WiFi RRM Simulator.

Models the hardware characteristics of the RF receiver. Consumes the channel
loss and computes received power (RSSI), thermal noise, and Signal-to-Interference-
Plus-Noise Ratio (SINR).

Sources:
    - Wireless hardware receiver design principles.
"""

import math
from typing import List

from src.realistic_simulator.constants import (
    THERMAL_NOISE_DENSITY_DBM_HZ,
    linear_to_db,
    dbm_to_mw
)


class ReceiverModel:
    """Models hardware reception characteristics to compute SINR."""

    def __init__(self, noise_figure_db: float):
        """
        Args:
            noise_figure_db: Receiver Noise Figure (NF) in dB.
        """
        self.noise_figure_db = noise_figure_db

    def thermal_noise_floor_dbm(self, bandwidth_hz: float) -> float:
        """
        Computes the thermal noise floor for a given bandwidth.

        Formula:
            N = -174 dBm/Hz + 10 * log10(Bandwidth) + NoiseFigure

        Args:
            bandwidth_hz: Channel bandwidth in Hertz.

        Returns:
            Noise floor power in dBm.
        """
        if bandwidth_hz <= 0:
            return float('-inf')
        
        # N = kTB (in dBm) + NF
        return THERMAL_NOISE_DENSITY_DBM_HZ + 10.0 * math.log10(bandwidth_hz) + self.noise_figure_db

    def compute_rssi(self, tx_power_dbm: float, tx_antenna_gain_dbi: float,
                     rx_antenna_gain_dbi: float, total_channel_loss_db: float) -> float:
        """
        Computes the Received Signal Strength Indicator (RSSI).

        Formula (Link Budget):
            RSSI = TxPower + TxGain + RxGain - ChannelLoss

        Args:
            tx_power_dbm: Transmit power in dBm.
            tx_antenna_gain_dbi: Transmitter antenna gain in dBi.
            rx_antenna_gain_dbi: Receiver antenna gain in dBi.
            total_channel_loss_db: Total loss from Channel Model in dB.

        Returns:
            RSSI in dBm.
        """
        return tx_power_dbm + tx_antenna_gain_dbi + rx_antenna_gain_dbi - total_channel_loss_db

    def compute_snr(self, rssi_dbm: float, noise_floor_dbm: float) -> float:
        """
        Computes the Signal-to-Noise Ratio (SNR).

        Formula:
            SNR(dB) = RSSI(dBm) - NoiseFloor(dBm)

        Args:
            rssi_dbm: Received signal power.
            noise_floor_dbm: Receiver noise floor.

        Returns:
            SNR in dB.
        """
        return rssi_dbm - noise_floor_dbm

    def compute_sinr(self, signal_power_dbm: float, noise_power_dbm: float,
                     interference_powers_dbm: List[float]) -> float:
        """
        Computes the Signal-to-Interference-Plus-Noise Ratio (SINR).

        Formula:
            SINR = P_signal / (P_noise + sum(P_interference))
            All additions must be performed in linear domain (milliwatts).

        Args:
            signal_power_dbm: Desired signal power in dBm (RSSI).
            noise_power_dbm: Thermal noise floor in dBm.
            interference_powers_dbm: List of interfering signal powers in dBm.

        Returns:
            SINR in dB.
        """
        signal_mw = dbm_to_mw(signal_power_dbm)
        noise_mw = dbm_to_mw(noise_power_dbm)
        
        interference_mw = sum(dbm_to_mw(p_dbm) for p_dbm in interference_powers_dbm)
        
        total_interference_and_noise_mw = noise_mw + interference_mw
        
        if total_interference_and_noise_mw <= 0:
            return float('inf')
            
        sinr_linear = signal_mw / total_interference_and_noise_mw
        return linear_to_db(sinr_linear)
