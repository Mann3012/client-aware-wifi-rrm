"""
Link Adaptation Module for the Client-Aware WiFi RRM Simulator.

Decoupled module for determining transmission parameters (MCS, Spatial Streams).
Currently implements a deterministic threshold-based algorithm. In the end-term,
this interface can be replaced with RL or Bayesian optimization.
"""

from typing import Optional

from src.realistic_simulator.constants import MCS_TABLE, MCSEntry


class LinkAdaptation:
    """Selects transmission parameters based on RF conditions."""

    def __init__(self, max_spatial_streams: int = 2):
        self.max_spatial_streams = max_spatial_streams

    def select_mcs(self, sinr_db: float, retry_rate: float = 0.0) -> MCSEntry:
        """
        Selects the highest Modulation and Coding Scheme (MCS) that can be
        reliably supported by the current SINR.

        In a real system, high retry rates cause rate fallback even if SINR
        appears sufficient. This deterministic model uses a threshold penalty.

        Args:
            sinr_db: Current Signal-to-Interference-Plus-Noise Ratio.
            retry_rate: Current frame retry rate (0.0 to 1.0).

        Returns:
            The selected MCSEntry.
        """
        # Apply an effective SINR penalty if retry rate is high (Rate Fallback)
        # E.g., 50% retries -> -5 dB penalty
        effective_sinr = sinr_db - (retry_rate * 10.0)

        # Iterate in reverse (highest to lowest MCS)
        for mcs in reversed(MCS_TABLE):
            if effective_sinr >= mcs.min_sinr_db:
                return mcs
        
        # Fallback to MCS 0 if SINR is very poor
        return MCS_TABLE[0]

    def select_spatial_streams(self, sinr_db: float, ap_nss: int, client_nss: int) -> int:
        """
        Selects the number of spatial streams (NSS).
        Requires high SINR to maintain multiple streams effectively.

        Args:
            sinr_db: Current SINR in dB.
            ap_nss: Max spatial streams supported by AP.
            client_nss: Max spatial streams supported by Client.

        Returns:
            Number of spatial streams (1 to max).
        """
        max_possible = min(ap_nss, client_nss, self.max_spatial_streams)
        
        if max_possible <= 1:
            return 1
            
        # Simplified MIMO logic: drop streams if SINR is poor
        if sinr_db < 15.0:
            return 1
        elif sinr_db < 25.0 and max_possible > 2:
            return 2
            
        return max_possible
