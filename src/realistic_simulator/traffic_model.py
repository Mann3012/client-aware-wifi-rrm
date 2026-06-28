"""
Traffic Model (Throughput & Latency Engine) for the Client-Aware WiFi RRM Simulator.

Converts effective MAC throughput into actual Layer-4 TCP/UDP throughput and
models queuing delays and jitter.

Implements the Mathis TCP throughput equation:
    Throughput = (MSS / RTT) * (C / sqrt(p))

Where:
    MSS = Maximum Segment Size
    RTT = Round Trip Time
    p = Packet Error Rate (Loss)
    C = Constant (~1.22)

Sources:
    - Mathis, M., Semke, J., Mahdavi, J., & Ott, T. (1997).
      "The macroscopic behavior of the TCP congestion avoidance algorithm."
"""

import math
from dataclasses import dataclass

from src.realistic_simulator.wifi6_phy import PhyResult
from src.realistic_simulator.mac_layer import MacResult


@dataclass
class TrafficResult:
    """Output metrics from the Traffic Model."""
    l4_throughput_mbps: float
    latency_ms: float
    jitter_ms: float
    demand_satisfied: bool


class TrafficModel:
    """Models application layer traffic behavior over the wireless link."""

    def __init__(self, mss_bytes: int = 1460):
        self.mss_bytes = mss_bytes

    def compute_mathis_tcp_throughput(
        self,
        base_rtt_ms: float,
        packet_loss_rate: float,
        link_capacity_mbps: float
    ) -> float:
        """
        Computes TCP throughput bounded by the Mathis equation and link capacity.

        Args:
            base_rtt_ms: Base Round Trip Time in milliseconds.
            packet_loss_rate: End-to-end packet loss probability (0.0 to 1.0).
            link_capacity_mbps: Maximum available MAC layer throughput.

        Returns:
            TCP throughput in Mbps.
        """
        if packet_loss_rate <= 0.0001:
            # Negligible loss, bottleneck is the link capacity
            return link_capacity_mbps
            
        rtt_seconds = max(0.001, base_rtt_ms / 1000.0)
        
        # Mathis Equation: Rate (bits/s) = (MSS_bits / RTT_s) * (1.22 / sqrt(p))
        mss_bits = self.mss_bytes * 8
        mathis_bps = (mss_bits / rtt_seconds) * (1.22 / math.sqrt(packet_loss_rate))
        
        mathis_mbps = mathis_bps / 1e6
        
        # TCP throughput cannot exceed the physical bottleneck
        return min(mathis_mbps, link_capacity_mbps)

    def compute_queuing_delay(self, demand_mbps: float, capacity_mbps: float) -> float:
        """
        Computes M/M/1 queuing delay approximation.
        
        Delay = 1 / (μ - λ)
        where μ is service rate and λ is arrival rate.
        
        Args:
            demand_mbps: Client traffic demand (λ).
            capacity_mbps: Link capacity (μ).
            
        Returns:
            Queuing delay in milliseconds.
        """
        if capacity_mbps <= 0.0:
            return float('inf')
            
        utilization = demand_mbps / capacity_mbps
        
        if utilization >= 0.99:
            # Overloaded queue (cap at 500ms for simulation sanity)
            return 500.0
            
        # Assume average packet size 1500 bytes for service rate calculation
        packet_size_bits = 1500 * 8
        service_rate_pkts_per_sec = (capacity_mbps * 1e6) / packet_size_bits
        arrival_rate_pkts_per_sec = (demand_mbps * 1e6) / packet_size_bits
        
        # M/M/1 delay in seconds = 1 / (μ - λ)
        delay_s = 1.0 / (service_rate_pkts_per_sec - arrival_rate_pkts_per_sec)
        
        return delay_s * 1000.0  # Convert to ms

    def evaluate_traffic(
        self,
        demand_mbps: float,
        phy_result: PhyResult,
        mac_result: MacResult,
        base_rtt_ms: float = 10.0,
        is_udp: bool = False
    ) -> TrafficResult:
        """
        Evaluates end-to-end traffic metrics for a single client.

        Args:
            demand_mbps: Requested application throughput.
            phy_result: Output from PHY layer.
            mac_result: Output from MAC layer.
            base_rtt_ms: Base network latency to destination.
            is_udp: If True, bypasses TCP congestion control (Mathis eq).

        Returns:
            TrafficResult with actual throughput and latency.
        """
        available_capacity = mac_result.effective_throughput_mbps
        
        if available_capacity <= 0:
            return TrafficResult(0.0, float('inf'), float('inf'), False)

        # 1. Throughput Calculation
        if is_udp:
            # UDP just blasts until capacity is reached
            actual_throughput = min(demand_mbps, available_capacity * (1.0 - phy_result.per))
        else:
            # TCP reacts to drops
            actual_throughput = self.compute_mathis_tcp_throughput(
                base_rtt_ms=base_rtt_ms,
                packet_loss_rate=phy_result.per,
                link_capacity_mbps=min(demand_mbps, available_capacity)
            )

        # 2. Latency Calculation (Base RTT + MAC Tx Time + Queuing Delay)
        mac_tx_time_ms = mac_result.total_frame_time_us / 1000.0
        queuing_delay_ms = self.compute_queuing_delay(demand_mbps, available_capacity)
        
        total_latency_ms = base_rtt_ms + mac_tx_time_ms + queuing_delay_ms
        
        # 3. Jitter Calculation (Stochastic variance of delay)
        # Higher PER or higher queuing leads to higher jitter
        jitter_ms = (queuing_delay_ms * 0.2) + (phy_result.per * 50.0)

        # 4. Demand Satisfaction
        demand_satisfied = actual_throughput >= (demand_mbps * 0.9)

        return TrafficResult(
            l4_throughput_mbps=actual_throughput,
            latency_ms=total_latency_ms,
            jitter_ms=jitter_ms,
            demand_satisfied=demand_satisfied
        )
