"""
IEEE 802.11ax PHY Layer Model for the Client-Aware WiFi RRM Simulator.

Models the complete dependency chain for Wi-Fi 6 PHY parameters:
Bandwidth → FFT Size → Subcarriers → Resource Units → MCS → PHY Rate.

Exposes interfaces for OFDMA scheduling, MU-MIMO, and BSS coloring,
which can be fully implemented in the end-term phase.

Sources:
    - IEEE 802.11ax-2021 (Wi-Fi 6) standard specification.
"""

from typing import Dict, List, Protocol
import math

from src.realistic_simulator.constants import (
    BANDWIDTH_PARAMS,
    SUBCARRIER_SPACING_KHZ,
    OFDM_DATA_SYMBOL_DURATION_US,
    MCSEntry,
    SubcarrierAllocation
)
from src.realistic_simulator.models import ClientState, APState


class WiFi6PhyConfig:
    """Encodes the deterministic IEEE 802.11ax PHY parameter hierarchy."""

    @staticmethod
    def get_subcarrier_allocation(bandwidth_mhz: int) -> SubcarrierAllocation:
        """Returns the subcarrier allocation (FFT size, data, pilots) for a bandwidth."""
        if bandwidth_mhz not in BANDWIDTH_PARAMS:
            raise ValueError(f"Unsupported bandwidth: {bandwidth_mhz} MHz")
        return BANDWIDTH_PARAMS[bandwidth_mhz]

    @staticmethod
    def ofdm_symbol_duration_us(guard_interval_us: float) -> float:
        """T_sym = 12.8 μs + GI."""
        return OFDM_DATA_SYMBOL_DURATION_US + guard_interval_us


class PhyResult:
    """Output metrics from PHY computation."""
    def __init__(self, mcs_index: int, phy_rate_mbps: float, per: float, 
                 spatial_streams: int, guard_interval_us: float):
        self.mcs_index = mcs_index
        self.phy_rate_mbps = phy_rate_mbps
        self.per = per
        self.spatial_streams = spatial_streams
        self.guard_interval_us = guard_interval_us


class WiFi6Phy:
    """Computes PHY-layer metrics following the 802.11ax hierarchy."""

    def __init__(self, bandwidth_mhz: int, spatial_streams: int, guard_interval_us: float):
        self.bandwidth = bandwidth_mhz
        self.alloc = WiFi6PhyConfig.get_subcarrier_allocation(bandwidth_mhz)
        self.nsd = self.alloc.data_subcarriers
        self.nss = spatial_streams
        self.gi = guard_interval_us
        self.symbol_duration_us = WiFi6PhyConfig.ofdm_symbol_duration_us(guard_interval_us)

    def compute_phy_rate_mbps(self, mcs: MCSEntry) -> float:
        """
        Computes the theoretical PHY data rate.

        Formula:
            Rate = (Nsd * Nbpscs * R * Nss) / T_sym

        Args:
            mcs: The selected MCSEntry.

        Returns:
            PHY rate in Mbps.
        """
        # Exact calculation: Nbpscs = log2(M) * (R_num / R_den)
        exact_bpscs = math.log2(mcs.modulation_order) * (mcs.coding_rate_num / mcs.coding_rate_den)
        bits_per_symbol = self.nsd * exact_bpscs * self.nss
        
        # Rate in bps = bits_per_symbol / (T_sym in seconds)
        rate_bps = bits_per_symbol / (self.symbol_duration_us * 1e-6)
        
        return rate_bps / 1e6  # Return in Mbps

    def compute_per(self, sinr_db: float, mcs: MCSEntry, packet_length_bytes: int = 1500) -> float:
        """
        Computes the Packet Error Rate (PER).

        This is an approximation using empirical curves.
        In reality, BER = f(SINR, Modulation).
        PER = 1 - (1 - BER)^L where L is packet length in bits.

        Args:
            sinr_db: Signal-to-Interference-Plus-Noise Ratio in dB.
            mcs: The selected MCSEntry.
            packet_length_bytes: Length of the packet payload.

        Returns:
            Packet Error Rate (0.0 to 1.0).
        """
        # Margin from the minimum required SINR
        margin_db = sinr_db - mcs.min_sinr_db
        
        if margin_db > 3.0:
            return 0.001  # Very low error floor
        elif margin_db < -3.0:
            return 0.999  # Almost total loss
            
        # Linear approximation across the waterfall region (approx 6 dB wide)
        # 3 dB margin -> 0% error, -3 dB margin -> 100% error
        per = 0.5 - (margin_db / 6.0)
        return max(0.001, min(0.999, per))

    def compute(self, sinr_db: float, mcs: MCSEntry, packet_length_bytes: int = 1500) -> PhyResult:
        """
        Executes the full PHY computation chain.

        Args:
            sinr_db: Measured SINR in dB.
            mcs: MCSEntry selected by the Link Adaptation module.
            packet_length_bytes: Size of packets transmitted.

        Returns:
            PhyResult object containing rate and error probability.
        """
        phy_rate = self.compute_phy_rate_mbps(mcs)
        per = self.compute_per(sinr_db, mcs, packet_length_bytes)
        
        return PhyResult(
            mcs_index=mcs.index,
            phy_rate_mbps=phy_rate,
            per=per,
            spatial_streams=self.nss,
            guard_interval_us=self.gi
        )


# ─────────────────────────────────────────────────────────────────────────────
# Future Plug-in Interfaces (End-Term)
# ─────────────────────────────────────────────────────────────────────────────

class OfdmaScheduler(Protocol):
    """Interface for OFDMA multi-user scheduling (end-term)."""
    def allocate_rus(self, clients: List[ClientState],
                     bandwidth_mhz: int) -> Dict[str, int]:
        """Map client_id → RU size (number of subcarriers)."""
        ...

class MimoStrategy(Protocol):
    """Interface for MU-MIMO beamforming (end-term)."""
    def compute_spatial_gain(self, ap: APState,
                             clients: List[ClientState]) -> Dict[str, float]:
        """Map client_id → Beamforming gain in dB."""
        ...

class SpatialReusePolicy(Protocol):
    """Interface for BSS Coloring / OBSS-PD (end-term)."""
    def should_defer(self, detected_bss_color: int, own_bss_color: int,
                     detected_rssi_dbm: float, obss_pd_threshold_dbm: float) -> bool:
        """Whether to defer transmission based on spatial reuse rules."""
        ...
