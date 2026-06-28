"""
Interference Engine for the Client-Aware WiFi RRM Simulator.

Models Co-Channel Interference (CCI), Adjacent Channel Interference (ACI),
and non-WiFi external interference sources (Microwave, Bluetooth).
Incorporates duty cycle and bandwidth overlap calculations.
"""

from typing import List, Optional
import math

from src.realistic_simulator.environment import WirelessEnvironment, InterferenceSource
from src.realistic_simulator.propagation import PropagationEngine
from src.realistic_simulator.constants import InterferenceType, CHANNEL_TO_FREQ_MHZ


class InterferenceEngine:
    """Calculates aggregate interference levels at specific receiver points."""

    def __init__(self, environment: WirelessEnvironment, propagation: PropagationEngine):
        self.env = environment
        self.prop = propagation

    def calculate_frequency_overlap(
        self,
        rx_freq_mhz: float,
        rx_bw_mhz: float,
        tx_freq_mhz: float,
        tx_bw_mhz: float
    ) -> float:
        """
        Calculates the percentage of power leaking from TX to RX based on frequency overlap.
        Simplified model assuming rectangular spectral masks.

        Returns:
            Overlap factor (0.0 to 1.0).
        """
        rx_start = rx_freq_mhz - (rx_bw_mhz / 2.0)
        rx_end = rx_freq_mhz + (rx_bw_mhz / 2.0)
        
        tx_start = tx_freq_mhz - (tx_bw_mhz / 2.0)
        tx_end = tx_freq_mhz + (tx_bw_mhz / 2.0)

        # No overlap
        if tx_end <= rx_start or tx_start >= rx_end:
            return 0.0

        # Full overlap (TX completely inside RX)
        if tx_start >= rx_start and tx_end <= rx_end:
            return 1.0

        # Partial overlap
        overlap_start = max(rx_start, tx_start)
        overlap_end = min(rx_end, tx_end)
        overlap_bw = overlap_end - overlap_start

        return overlap_bw / tx_bw_mhz

    def compute_external_interference(
        self,
        rx_location: "Point",
        rx_freq_mhz: float,
        rx_bw_mhz: float,
        sim_time_s: float = 0.0
    ) -> List[float]:
        """
        Computes the received power from active non-WiFi interference sources.

        Args:
            rx_location: The location of the receiver (AP or Client).
            rx_freq_mhz: Center frequency of the receiver.
            rx_bw_mhz: Bandwidth of the receiver.
            sim_time_s: Current simulation timestamp.

        Returns:
            List of interference powers in dBm for each overlapping source.
        """
        active_sources = self.env.active_interference_sources(sim_time_s)
        interference_powers = []

        for source in active_sources:
            overlap = self.calculate_frequency_overlap(
                rx_freq_mhz, rx_bw_mhz,
                source.frequency_mhz, source.bandwidth_mhz
            )
            
            if overlap <= 0.0:
                continue

            # Calculate deterministic path loss from source to receiver
            path_loss_db = self.prop.total_path_loss(
                point_a=source.location,
                point_b=rx_location,
                freq_hz=source.frequency_mhz * 1e6,
                path_loss_exponent=3.0  # Assumed standard indoor
            )

            # Received Power = TX - PathLoss + 10*log10(Overlap * DutyCycle)
            # This averages the bursty power over the measurement window
            effective_fraction = overlap * source.duty_cycle
            if effective_fraction <= 0.0:
                continue
                
            rx_power_dbm = source.tx_power_dbm - path_loss_db + 10.0 * math.log10(effective_fraction)
            
            # Floor very weak signals to avoid math instability
            if rx_power_dbm > -120.0:
                interference_powers.append(rx_power_dbm)

        return interference_powers
