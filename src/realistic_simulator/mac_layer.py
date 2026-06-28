"""
Medium Access Control (MAC) Layer Model for the Client-Aware WiFi RRM Simulator.

Models the 802.11ax CSMA/CA protocol overhead to translate PHY data rates into
effective MAC efficiency and exact frame transmission times.

Calculates:
- DCF Contention Overhead (DIFS + Backoff)
- RTS/CTS Exchange Overhead
- Preamble and PHY Header Overheads
- SIFS + ACK Overheads
- Effective MAC Efficiency

Sources:
    - IEEE 802.11ax-2021 Section 27.3
"""

from typing import Optional
from dataclasses import dataclass

from src.realistic_simulator.constants import (
    SLOT_TIME_US,
    SIFS_DURATION_US,
    DIFS_DURATION_US,
    HE_PREAMBLE_DURATION_US,
    PHY_HEADER_DURATION_US,
    ACK_FRAME_DURATION_US,
    CW_MIN,
    CW_MAX,
)
from src.realistic_simulator.wifi6_phy import PhyResult


@dataclass
class MacResult:
    """Output metrics from MAC computation."""
    total_frame_time_us: float
    payload_time_us: float
    overhead_time_us: float
    mac_efficiency: float      # Payload Time / Total Time
    effective_throughput_mbps: float


class MacLayer:
    """Models 802.11ax MAC layer timing and efficiency."""

    def __init__(self, rts_cts_threshold_bytes: int = 2347):
        """
        Args:
            rts_cts_threshold_bytes: Packets larger than this use RTS/CTS.
                                     Default 2347 means practically off for standard frames.
        """
        self.rts_cts_threshold_bytes = rts_cts_threshold_bytes

    def average_backoff_us(self, collision_probability: float) -> float:
        """
        Computes the average contention window backoff time based on collision probability.
        
        Uses a simplified Markov chain approximation: 
        E[CW] ≈ CW_min * (1 + 2*p) for small p.

        Args:
            collision_probability: Probability of collision (0.0 to 1.0).

        Returns:
            Average backoff duration in microseconds.
        """
        # Truncated binary exponential backoff approximation
        # For p=0, average slots = CW_MIN / 2 = 7.5
        cw = min(CW_MAX, float(CW_MIN) * (2.0 ** (collision_probability * 10.0)))
        average_slots = cw / 2.0
        return average_slots * SLOT_TIME_US

    def compute_rts_cts_overhead_us(self, base_rate_mbps: float = 6.0) -> float:
        """
        Computes the time taken by an RTS/CTS exchange.
        
        RTS Frame: 20 bytes
        CTS Frame: 14 bytes
        
        Args:
            base_rate_mbps: PHY rate used for control frames (typically lowest mandatory rate).
            
        Returns:
            RTS/CTS exchange duration in microseconds.
        """
        # Time = Preamble + Header + Payload / Rate
        rts_payload_us = (20 * 8) / base_rate_mbps
        cts_payload_us = (14 * 8) / base_rate_mbps
        
        rts_time = HE_PREAMBLE_DURATION_US + PHY_HEADER_DURATION_US + rts_payload_us
        cts_time = HE_PREAMBLE_DURATION_US + PHY_HEADER_DURATION_US + cts_payload_us
        
        return rts_time + SIFS_DURATION_US + cts_time + SIFS_DURATION_US

    def compute_transmission_time(
        self,
        packet_length_bytes: int,
        phy_result: PhyResult,
        collision_probability: float = 0.0,
        aggregated_frames: int = 1
    ) -> MacResult:
        """
        Computes the exact time required to successfully transmit an A-MPDU packet
        and the resulting MAC efficiency.

        Timing Diagram:
        [DIFS] + [Backoff] + [RTS + SIFS + CTS + SIFS]* + [Preamble + PHY_Hdr + MAC_Hdr + Payload] + [SIFS] + [ACK]

        Args:
            packet_length_bytes: Size of a single IP packet payload.
            phy_result: Output from the PHY layer computation.
            collision_probability: Current medium collision probability.
            aggregated_frames: Number of frames in the A-MPDU (Frame Aggregation).

        Returns:
            MacResult detailing timing and efficiency.
        """
        # 1. Contention Overhead
        backoff_us = self.average_backoff_us(collision_probability)
        contention_us = DIFS_DURATION_US + backoff_us
        
        # 2. RTS/CTS Overhead
        total_payload_bytes = packet_length_bytes * aggregated_frames
        rts_cts_us = 0.0
        if total_payload_bytes > self.rts_cts_threshold_bytes:
            rts_cts_us = self.compute_rts_cts_overhead_us()
            
        # 3. Payload Time
        # MAC Header = 36 bytes per frame (QoS Data)
        mac_header_bytes = 36 * aggregated_frames
        total_bits = (total_payload_bytes + mac_header_bytes) * 8
        
        if phy_result.phy_rate_mbps <= 0:
            return MacResult(0.0, 0.0, 0.0, 0.0, 0.0)
            
        # Payload transmission time at selected PHY rate
        payload_tx_us = total_bits / phy_result.phy_rate_mbps
        
        # 4. Total Frame Time
        overhead_us = contention_us + rts_cts_us + HE_PREAMBLE_DURATION_US + PHY_HEADER_DURATION_US + SIFS_DURATION_US + ACK_FRAME_DURATION_US
        
        # If there are retries, overhead and payload time increases.
        # E[Tx] = T_success + (PER / (1 - PER)) * T_fail
        # We approximate T_fail ≈ T_success without the final ACK.
        expected_transmissions = 1.0 / max(0.0001, (1.0 - phy_result.per))
        
        total_frame_time_us = (overhead_us + payload_tx_us) * expected_transmissions
        
        # Efficiency
        # Useful time is ONLY the IP payload bits
        useful_time_us = (total_payload_bytes * 8) / phy_result.phy_rate_mbps
        
        mac_efficiency = useful_time_us / max(0.001, total_frame_time_us)
        effective_throughput_mbps = phy_result.phy_rate_mbps * mac_efficiency
        
        return MacResult(
            total_frame_time_us=total_frame_time_us,
            payload_time_us=payload_tx_us * expected_transmissions,
            overhead_time_us=(overhead_us * expected_transmissions) + (payload_tx_us * (expected_transmissions - 1)),
            mac_efficiency=mac_efficiency,
            effective_throughput_mbps=effective_throughput_mbps
        )
