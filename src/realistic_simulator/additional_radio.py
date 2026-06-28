"""
Additional (Sensing) Radio Model for the Client-Aware WiFi RRM Simulator.

Models a dedicated sensing radio that operates independently from the serving
radio. Produces spectrum analysis data including:
- FFT power snapshots across the channel bandwidth
- Interference source classification (WiFi vs Non-WiFi)
- Duty cycle estimation per detected interferer
- Channel occupancy measurements

In Arista's architecture, the additional radio continuously scans all channels
while the serving radio maintains client connections. This separation allows
RRM decisions to be informed by spectrum data without impacting client service.

Sources:
    - Arista Networks Cognitive WiFi documentation
    - IEEE 802.11ax-2021 Section 27 (Spectrum Management)
"""

import math
import random
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

from src.realistic_simulator.constants import (
    BANDWIDTH_PARAMS,
    SUBCARRIER_SPACING_KHZ,
    THERMAL_NOISE_DENSITY_DBM_HZ,
    CHANNEL_TO_FREQ_MHZ,
    dbm_to_mw,
    mw_to_dbm,
    InterferenceType,
)
from src.realistic_simulator.environment import WirelessEnvironment, Point

logger = logging.getLogger("RRM.SensingRadio")


# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FFTBin:
    """A single FFT frequency bin measurement."""
    freq_mhz: float
    power_dbm: float


@dataclass
class SpectrumSnapshot:
    """A complete FFT snapshot across the channel bandwidth.
    
    Represents a single sweep of the sensing radio's spectrum analyzer,
    capturing power levels at each frequency bin across the monitored
    channel bandwidth.
    """
    channel: int
    center_freq_mhz: float
    bandwidth_mhz: int
    bins: List[FFTBin] = field(default_factory=list)
    noise_floor_dbm: float = -95.0
    peak_power_dbm: float = -95.0
    avg_power_dbm: float = -95.0
    channel_busy_fraction: float = 0.0

    def to_dict(self) -> dict:
        return {
            "channel": self.channel,
            "center_freq_mhz": self.center_freq_mhz,
            "bandwidth_mhz": self.bandwidth_mhz,
            "noise_floor_dbm": round(self.noise_floor_dbm, 2),
            "peak_power_dbm": round(self.peak_power_dbm, 2),
            "avg_power_dbm": round(self.avg_power_dbm, 2),
            "channel_busy_fraction": round(self.channel_busy_fraction, 4),
            "num_bins": len(self.bins),
        }


@dataclass
class DetectedInterferer:
    """A classified interference source detected by the sensing radio."""
    classification: str       # "wifi", "microwave", "bluetooth", "unknown"
    center_freq_mhz: float
    bandwidth_mhz: float
    power_dbm: float
    duty_cycle: float         # Estimated active fraction (0.0 to 1.0)
    confidence: float         # Classification confidence (0.0 to 1.0)

    def to_dict(self) -> dict:
        return {
            "classification": self.classification,
            "center_freq_mhz": round(self.center_freq_mhz, 1),
            "bandwidth_mhz": round(self.bandwidth_mhz, 1),
            "power_dbm": round(self.power_dbm, 2),
            "duty_cycle": round(self.duty_cycle, 4),
            "confidence": round(self.confidence, 3),
        }


@dataclass
class SensingRadioReport:
    """Complete output from a sensing radio measurement cycle."""
    spectrum: SpectrumSnapshot
    detected_interferers: List[DetectedInterferer] = field(default_factory=list)
    channel_quality_score: float = 100.0  # 0-100, higher is cleaner

    def to_dict(self) -> dict:
        return {
            "spectrum": self.spectrum.to_dict(),
            "detected_interferers": [d.to_dict() for d in self.detected_interferers],
            "channel_quality_score": round(self.channel_quality_score, 1),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Sensing Radio Engine
# ─────────────────────────────────────────────────────────────────────────────

class SensingRadio:
    """Models an additional/sensing radio performing independent spectrum analysis.

    The sensing radio operates on a separate RF chain from the serving radio.
    It performs periodic spectrum sweeps, classifies detected energy, and
    estimates channel quality metrics that feed into the RRM analytics pipeline.
    """

    # Classification thresholds
    WIFI_SIGNAL_BW_MHZ = 20.0        # Minimum bandwidth for a WiFi signal
    BT_SIGNAL_BW_MHZ = 2.0           # Bluetooth signal bandwidth
    MICROWAVE_BW_MIN_MHZ = 10.0      # Minimum microwave leakage bandwidth
    DETECTION_THRESHOLD_DB = 6.0     # Signal must be this far above noise floor

    def __init__(self, noise_figure_db: float = 5.0):
        self.noise_figure_db = noise_figure_db

    def compute_thermal_floor(self, bandwidth_hz: float) -> float:
        """Computes the thermal noise floor for the sensing radio."""
        if bandwidth_hz <= 0:
            return -150.0
        return THERMAL_NOISE_DENSITY_DBM_HZ + 10.0 * math.log10(bandwidth_hz) + self.noise_figure_db

    def perform_fft_sweep(
        self,
        channel: int,
        bandwidth_mhz: int,
        environment: WirelessEnvironment,
        ap_location: Point,
        sim_time_s: float = 0.0,
    ) -> SpectrumSnapshot:
        """Performs an FFT sweep across the specified channel bandwidth.

        Generates per-bin power measurements by computing the thermal noise
        floor and overlaying any active interference sources.

        Args:
            channel: WiFi channel number.
            bandwidth_mhz: Channel bandwidth in MHz.
            environment: The wireless environment containing interference sources.
            ap_location: Location of the sensing radio (co-located with AP).
            sim_time_s: Current simulation timestamp.

        Returns:
            SpectrumSnapshot with per-bin power data and summary statistics.
        """
        if bandwidth_mhz not in BANDWIDTH_PARAMS:
            bandwidth_mhz = 20

        alloc = BANDWIDTH_PARAMS[bandwidth_mhz]
        num_bins = alloc.fft_size
        center_freq_mhz = CHANNEL_TO_FREQ_MHZ.get(channel, 5180.0)

        # Subcarrier spacing in MHz
        sc_spacing_mhz = SUBCARRIER_SPACING_KHZ / 1000.0

        # Per-bin thermal noise floor
        bin_bw_hz = sc_spacing_mhz * 1e6
        bin_noise_floor_dbm = self.compute_thermal_floor(bin_bw_hz)

        bins: List[FFTBin] = []
        total_power_mw = 0.0
        peak_power_dbm = -150.0
        busy_bins = 0

        # Get active interference sources
        active_sources = environment.active_interference_sources(sim_time_s)

        for i in range(num_bins):
            # Frequency of this bin
            bin_freq_mhz = center_freq_mhz - (bandwidth_mhz / 2.0) + (i * sc_spacing_mhz)

            # Start with thermal noise + small random variation
            bin_power_mw = dbm_to_mw(bin_noise_floor_dbm + random.gauss(0, 0.5))

            # Add contributions from active interference sources
            for src in active_sources:
                src_start = src.frequency_mhz - (src.bandwidth_mhz / 2.0)
                src_end = src.frequency_mhz + (src.bandwidth_mhz / 2.0)

                if src_start <= bin_freq_mhz <= src_end:
                    # Compute path loss from source to AP (sensing radio location)
                    dist = ap_location.distance_to(src.location)
                    if dist < 0.5:
                        dist = 0.5

                    # Simplified path loss for interference
                    pl_db = 40.0 + 30.0 * math.log10(max(1.0, dist))

                    # Received power from this interferer at this bin
                    intf_power_dbm = src.tx_power_dbm - pl_db
                    # Apply duty cycle as probabilistic presence
                    if random.random() < src.duty_cycle:
                        bin_power_mw += dbm_to_mw(intf_power_dbm)

            bin_power_dbm = mw_to_dbm(bin_power_mw)
            bins.append(FFTBin(freq_mhz=round(bin_freq_mhz, 3), power_dbm=round(bin_power_dbm, 2)))

            total_power_mw += bin_power_mw
            peak_power_dbm = max(peak_power_dbm, bin_power_dbm)

            # A bin is "busy" if its power exceeds the noise floor by the detection threshold
            if bin_power_dbm > bin_noise_floor_dbm + self.DETECTION_THRESHOLD_DB:
                busy_bins += 1

        avg_power_dbm = mw_to_dbm(total_power_mw / max(1, num_bins))
        channel_busy_fraction = busy_bins / max(1, num_bins)

        return SpectrumSnapshot(
            channel=channel,
            center_freq_mhz=center_freq_mhz,
            bandwidth_mhz=bandwidth_mhz,
            bins=bins,
            noise_floor_dbm=round(bin_noise_floor_dbm, 2),
            peak_power_dbm=round(peak_power_dbm, 2),
            avg_power_dbm=round(avg_power_dbm, 2),
            channel_busy_fraction=round(channel_busy_fraction, 4),
        )

    def classify_interferers(
        self, snapshot: SpectrumSnapshot
    ) -> List[DetectedInterferer]:
        """Classifies energy detected above the noise floor into interferer types.

        Uses bandwidth, center frequency, and duty cycle heuristics to
        distinguish WiFi, Bluetooth, and Microwave sources.

        Args:
            snapshot: A completed SpectrumSnapshot from perform_fft_sweep.

        Returns:
            List of DetectedInterferer objects.
        """
        if not snapshot.bins:
            return []

        noise_floor = snapshot.noise_floor_dbm
        threshold = noise_floor + self.DETECTION_THRESHOLD_DB

        # Find contiguous regions of elevated power
        regions: List[List[FFTBin]] = []
        current_region: List[FFTBin] = []

        for fft_bin in snapshot.bins:
            if fft_bin.power_dbm > threshold:
                current_region.append(fft_bin)
            else:
                if current_region:
                    regions.append(current_region)
                    current_region = []
        if current_region:
            regions.append(current_region)

        # Classify each region
        detected: List[DetectedInterferer] = []
        sc_spacing_mhz = SUBCARRIER_SPACING_KHZ / 1000.0

        for region in regions:
            region_bw_mhz = len(region) * sc_spacing_mhz
            center = (region[0].freq_mhz + region[-1].freq_mhz) / 2.0
            peak = max(b.power_dbm for b in region)
            avg_power = mw_to_dbm(
                sum(dbm_to_mw(b.power_dbm) for b in region) / len(region)
            )

            # Duty cycle estimation: fraction of bins in region above threshold
            active_bins = sum(1 for b in region if b.power_dbm > threshold)
            duty_cycle = active_bins / max(1, len(region))

            # Classification heuristics
            if region_bw_mhz >= self.WIFI_SIGNAL_BW_MHZ:
                classification = "wifi"
                confidence = min(1.0, region_bw_mhz / 20.0) * 0.85
            elif region_bw_mhz <= self.BT_SIGNAL_BW_MHZ + 0.5:
                classification = "bluetooth"
                confidence = 0.75
            elif region_bw_mhz >= self.MICROWAVE_BW_MIN_MHZ:
                classification = "microwave"
                confidence = 0.80
            else:
                classification = "unknown"
                confidence = 0.50

            detected.append(DetectedInterferer(
                classification=classification,
                center_freq_mhz=center,
                bandwidth_mhz=region_bw_mhz,
                power_dbm=peak,
                duty_cycle=duty_cycle,
                confidence=confidence,
            ))

        return detected

    def compute_channel_quality(
        self, snapshot: SpectrumSnapshot, interferers: List[DetectedInterferer]
    ) -> float:
        """Computes a 0-100 channel quality score.

        Factors:
        - Channel busy fraction (higher = worse)
        - Number and power of detected interferers
        - Peak-to-noise-floor ratio

        Args:
            snapshot: The spectrum snapshot.
            interferers: Classified interferers.

        Returns:
            Channel quality score (0-100, higher is cleaner).
        """
        # Start at 100
        score = 100.0

        # Penalty for channel busy fraction (up to -40 points)
        score -= snapshot.channel_busy_fraction * 40.0

        # Penalty for each interferer based on power above noise floor
        for intf in interferers:
            excess_db = max(0, intf.power_dbm - snapshot.noise_floor_dbm)
            # Each dB above noise floor costs 1 point, scaled by duty cycle
            score -= min(20.0, excess_db * intf.duty_cycle * 0.5)

        # Penalty for high peak power (up to -10 points)
        peak_excess = max(0, snapshot.peak_power_dbm - snapshot.noise_floor_dbm - 10.0)
        score -= min(10.0, peak_excess * 0.5)

        return max(0.0, min(100.0, score))

    def scan(
        self,
        channel: int,
        bandwidth_mhz: int,
        environment: WirelessEnvironment,
        ap_location: Point,
        sim_time_s: float = 0.0,
    ) -> SensingRadioReport:
        """Performs a complete sensing radio measurement cycle.

        This is the main entry point. It performs an FFT sweep, classifies
        detected interferers, and computes a channel quality score.

        Args:
            channel: WiFi channel number to scan.
            bandwidth_mhz: Channel bandwidth.
            environment: Wireless environment with interference sources.
            ap_location: AP/sensing radio location.
            sim_time_s: Current simulation time.

        Returns:
            SensingRadioReport with spectrum, interferers, and quality score.
        """
        spectrum = self.perform_fft_sweep(
            channel, bandwidth_mhz, environment, ap_location, sim_time_s
        )
        interferers = self.classify_interferers(spectrum)
        quality = self.compute_channel_quality(spectrum, interferers)

        logger.debug(
            "Sensing scan ch=%d bw=%dMHz: busy=%.1f%%, interferers=%d, quality=%.1f",
            channel, bandwidth_mhz,
            spectrum.channel_busy_fraction * 100,
            len(interferers), quality,
        )

        return SensingRadioReport(
            spectrum=spectrum,
            detected_interferers=interferers,
            channel_quality_score=quality,
        )
