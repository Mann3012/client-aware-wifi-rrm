"""
Centralized Engineering Constants for the Client-Aware WiFi RRM Simulator.

All numerical constants used throughout the simulator are defined here.
No magic numbers should appear anywhere else in the codebase.

Sources:
    - IEEE 802.11ax-2021 (Wi-Fi 6)
    - ITU-R P.1238-10 (Indoor propagation)
    - Rappaport, "Wireless Communications: Principles and Practice", 2nd Ed.
    - Goldsmith, "Wireless Communications", Cambridge University Press.
    - Cisco Wireless Design Best Practices.
"""

import math
from enum import Enum
from typing import NamedTuple, Dict, List, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# Physical Constants
# ─────────────────────────────────────────────────────────────────────────────

SPEED_OF_LIGHT_MPS: float = 299_792_458.0
"""Speed of light in meters per second (m/s)."""

BOLTZMANN_CONSTANT_JK: float = 1.380649e-23
"""Boltzmann constant in Joules per Kelvin (J/K)."""

STANDARD_TEMPERATURE_K: float = 290.0
"""Standard room temperature in Kelvin (IEEE reference)."""

THERMAL_NOISE_DENSITY_DBM_HZ: float = -174.0
"""Thermal noise power spectral density at 290K: kTB in dBm/Hz.
   N0 = 10*log10(k*T*1000) = 10*log10(1.38e-23 * 290 * 1000) ≈ -174 dBm/Hz."""


# ─────────────────────────────────────────────────────────────────────────────
# Wall Material Attenuation
# Source: ITU-R P.1238-10 Table 3, Cisco Wireless Design Guide
# ─────────────────────────────────────────────────────────────────────────────

class WallMaterial(Enum):
    """Wall construction material types with typical attenuation ranges."""
    DRYWALL = "drywall"
    GLASS = "glass"
    WOOD = "wood"
    BRICK = "brick"
    CONCRETE = "concrete"
    METAL = "metal"


# Attenuation in dB: (min, typical, max)
WALL_ATTENUATION_DB: Dict[WallMaterial, Tuple[float, float, float]] = {
    WallMaterial.DRYWALL:  (3.0, 4.0, 5.0),
    WallMaterial.GLASS:    (2.0, 3.0, 4.0),
    WallMaterial.WOOD:     (3.0, 4.0, 6.0),
    WallMaterial.BRICK:    (8.0, 10.0, 12.0),
    WallMaterial.CONCRETE: (15.0, 18.0, 20.0),
    WallMaterial.METAL:    (20.0, 25.0, 35.0),
}
"""Per-material signal attenuation in dB. Source: ITU-R P.1238-10."""


# ─────────────────────────────────────────────────────────────────────────────
# Path Loss Exponents
# Source: Rappaport Table 4.2, ITU-R P.1238-10
# ─────────────────────────────────────────────────────────────────────────────

class EnvironmentType(Enum):
    """Indoor environment classifications affecting propagation."""
    FREE_SPACE = "free_space"
    OPEN_OFFICE = "open_office"
    INDOOR_OFFICE = "indoor_office"
    WAREHOUSE = "warehouse"
    CONCRETE_BUILDING = "concrete_building"
    CORRIDOR = "corridor"


# (path_loss_exponent_n, shadow_fading_std_dev_sigma_db)
PATH_LOSS_PARAMS: Dict[EnvironmentType, Tuple[float, float]] = {
    EnvironmentType.FREE_SPACE:        (2.0, 0.0),
    EnvironmentType.OPEN_OFFICE:       (2.5, 4.0),
    EnvironmentType.INDOOR_OFFICE:     (3.0, 5.0),
    EnvironmentType.WAREHOUSE:         (3.5, 6.0),
    EnvironmentType.CONCRETE_BUILDING: (4.0, 7.0),
    EnvironmentType.CORRIDOR:          (1.8, 3.0),
}
"""Path loss exponent (n) and shadow fading std dev (σ) per environment.
   Source: Rappaport Table 4.2."""


# ─────────────────────────────────────────────────────────────────────────────
# Frequency Band Definitions
# Source: IEEE 802.11ax-2021
# ─────────────────────────────────────────────────────────────────────────────

class FrequencyBand(Enum):
    """Wi-Fi operating frequency bands."""
    BAND_2_4_GHZ = "2.4GHz"
    BAND_5_GHZ = "5GHz"
    BAND_6_GHZ = "6GHz"


# Channel number → center frequency in MHz
CHANNEL_TO_FREQ_MHZ: Dict[int, float] = {
    # 2.4 GHz band (20 MHz channels)
    1: 2412.0, 2: 2417.0, 3: 2422.0, 4: 2427.0, 5: 2432.0,
    6: 2437.0, 7: 2442.0, 8: 2447.0, 9: 2452.0, 10: 2457.0,
    11: 2462.0, 12: 2467.0, 13: 2472.0, 14: 2484.0,
    # 5 GHz UNII-1
    36: 5180.0, 40: 5200.0, 44: 5220.0, 48: 5240.0,
    # 5 GHz UNII-2
    52: 5260.0, 56: 5280.0, 60: 5300.0, 64: 5320.0,
    # 5 GHz UNII-2 Extended
    100: 5500.0, 104: 5520.0, 108: 5540.0, 112: 5560.0,
    116: 5580.0, 120: 5600.0, 124: 5620.0, 128: 5640.0,
    132: 5660.0, 136: 5680.0, 140: 5700.0, 144: 5720.0,
    # 5 GHz UNII-3
    149: 5745.0, 153: 5765.0, 157: 5785.0, 161: 5805.0, 165: 5825.0,
    # 6 GHz (U-NII-5, partial — future-ready)
    1:  5955.0,  # Note: 6 GHz channel 1 overlaps with 2.4 GHz numbering
    # To avoid collision, 6 GHz channels use a separate lookup if needed
}

# Non-overlapping 2.4 GHz channels
NON_OVERLAPPING_2_4_GHZ: List[int] = [1, 6, 11]

# Common 5 GHz channels
COMMON_5_GHZ_CHANNELS: List[int] = [36, 40, 44, 48, 149, 153, 157, 161]


# ─────────────────────────────────────────────────────────────────────────────
# IEEE 802.11ax PHY Parameters
# Source: IEEE 802.11ax-2021 Table 27-64
# ─────────────────────────────────────────────────────────────────────────────

SUBCARRIER_SPACING_KHZ: float = 78.125
"""802.11ax subcarrier spacing: 78.125 kHz (4× longer OFDM symbol than 802.11ac)."""

OFDM_DATA_SYMBOL_DURATION_US: float = 12.8
"""802.11ax OFDM useful symbol duration: 12.8 μs."""

# Available guard intervals in μs
GUARD_INTERVALS_US: List[float] = [0.8, 1.6, 3.2]


class SubcarrierAllocation(NamedTuple):
    """Subcarrier distribution for a given channel bandwidth."""
    fft_size: int
    total_subcarriers: int
    data_subcarriers: int    # Nsd
    pilot_subcarriers: int
    null_guard_subcarriers: int


# Bandwidth (MHz) → FFT size, subcarrier counts
# Source: IEEE 802.11ax-2021 Table 27-6, Table 27-7
BANDWIDTH_PARAMS: Dict[int, SubcarrierAllocation] = {
    20:  SubcarrierAllocation(fft_size=256,  total_subcarriers=256,
                              data_subcarriers=234,  pilot_subcarriers=8,
                              null_guard_subcarriers=14),
    40:  SubcarrierAllocation(fft_size=512,  total_subcarriers=512,
                              data_subcarriers=468,  pilot_subcarriers=16,
                              null_guard_subcarriers=28),
    80:  SubcarrierAllocation(fft_size=1024, total_subcarriers=1024,
                              data_subcarriers=980,  pilot_subcarriers=16,
                              null_guard_subcarriers=28),
    160: SubcarrierAllocation(fft_size=2048, total_subcarriers=2048,
                              data_subcarriers=1960, pilot_subcarriers=32,
                              null_guard_subcarriers=56),
}

# Resource Unit (RU) sizes available in 802.11ax OFDMA
# Each RU size defines how many data subcarriers are allocated to one user
RESOURCE_UNIT_SIZES: List[int] = [26, 52, 106, 242, 484, 996]
"""Available RU sizes in 802.11ax (number of subcarriers per RU).
   A 20 MHz channel uses 242-tone RU for single user."""

# Full-bandwidth RU per channel width (single-user mode)
FULL_BW_RU: Dict[int, int] = {
    20: 242,
    40: 484,
    80: 996,
    160: 1960,  # 2×996 minus pilots
}


# ─────────────────────────────────────────────────────────────────────────────
# MCS Table — IEEE 802.11ax (MCS 0–11)
# Source: IEEE 802.11ax-2021 Table 27-64, Table 27-65
# ─────────────────────────────────────────────────────────────────────────────

class MCSEntry(NamedTuple):
    """A single row from the IEEE 802.11ax MCS table."""
    index: int
    modulation: str
    modulation_order: int   # M (number of constellation points)
    coding_rate_num: int    # Numerator of coding rate R
    coding_rate_den: int    # Denominator of coding rate R
    bits_per_subcarrier: float  # Nbpscs = log2(M) × R
    min_sinr_db: float      # Minimum SINR threshold for reliable reception


MCS_TABLE: List[MCSEntry] = [
    # index, modulation,   M,    R_num, R_den, Nbpscs,  min_sinr
    MCSEntry(0,  "BPSK",       2,    1, 2,  0.5,    -1.0),
    MCSEntry(1,  "QPSK",       4,    1, 2,  1.0,     2.0),
    MCSEntry(2,  "QPSK",       4,    3, 4,  1.5,     5.0),
    MCSEntry(3,  "16-QAM",    16,    1, 2,  2.0,     8.0),
    MCSEntry(4,  "16-QAM",    16,    3, 4,  3.0,    11.0),
    MCSEntry(5,  "64-QAM",    64,    2, 3,  4.0,    15.0),
    MCSEntry(6,  "64-QAM",    64,    3, 4,  4.5,    18.0),
    MCSEntry(7,  "64-QAM",    64,    5, 6,  5.0,    20.0),
    MCSEntry(8,  "256-QAM",  256,    3, 4,  6.0,    25.0),
    MCSEntry(9,  "256-QAM",  256,    5, 6,  6.67,   28.0),
    MCSEntry(10, "1024-QAM", 1024,   3, 4,  7.5,    30.0),
    MCSEntry(11, "1024-QAM", 1024,   5, 6,  8.33,   33.0),
]
"""IEEE 802.11ax MCS index 0–11 with modulation, coding rate, and SINR thresholds.
   Nbpscs (coded bits per subcarrier per stream) = log2(M) × R.
   SINR thresholds are approximate practical values for 10% PER at 1500-byte packets.
   Source: IEEE 802.11ax Table 27-64, Cisco Wireless LAN Design Guide."""


# ─────────────────────────────────────────────────────────────────────────────
# 802.11ax MAC Timing Constants
# Source: IEEE 802.11ax-2021 Section 27.3
# ─────────────────────────────────────────────────────────────────────────────

SLOT_TIME_US: float = 9.0
"""802.11ax slot time: 9 μs (same as 802.11n/ac for 5 GHz)."""

SIFS_DURATION_US: float = 16.0
"""Short Interframe Space: 16 μs."""

DIFS_DURATION_US: float = SIFS_DURATION_US + 2 * SLOT_TIME_US  # 34 μs
"""DCF Interframe Space: SIFS + 2×Slot = 34 μs."""

HE_PREAMBLE_DURATION_US: float = 100.0
"""HE (High Efficiency) preamble duration for 802.11ax: ~100 μs.
   Includes L-STF, L-LTF, L-SIG, RL-SIG, HE-SIG-A, HE-STF, HE-LTF.
   Source: IEEE 802.11ax Section 27.3.10."""

PHY_HEADER_DURATION_US: float = 20.0
"""PHY header overhead (service field + tail bits): ~20 μs."""

ACK_FRAME_DURATION_US: float = 44.0
"""Acknowledgement frame duration: ~44 μs (preamble + 14 bytes at base rate)."""

CW_MIN: int = 15
"""Minimum contention window size for 802.11ax."""

CW_MAX: int = 1023
"""Maximum contention window size for 802.11ax."""


# ─────────────────────────────────────────────────────────────────────────────
# Receiver Parameters
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_AP_NOISE_FIGURE_DB: float = 5.0
"""Typical Access Point receiver noise figure: 5 dB.
   Source: Qualcomm chipset datasheet, Cisco best practice."""

DEFAULT_CLIENT_NOISE_FIGURE_DB: float = 7.0
"""Typical client device receiver noise figure: 7 dB.
   Smartphones and laptops typically have higher NF than APs."""

DEFAULT_AP_TX_POWER_DBM: float = 20.0
"""Default AP transmit power: 20 dBm (100 mW). Common for enterprise APs."""

DEFAULT_AP_ANTENNA_GAIN_DBI: float = 3.0
"""Default AP antenna gain: 3 dBi (omnidirectional)."""

DEFAULT_CLIENT_ANTENNA_GAIN_DBI: float = 0.0
"""Default client antenna gain: 0 dBi (internal antenna)."""

DEFAULT_AP_SPATIAL_STREAMS: int = 2
"""Default number of spatial streams for AP: 2×2 MIMO."""


# ─────────────────────────────────────────────────────────────────────────────
# Multipath / Channel Model Defaults
# Source: ITU-R P.1238-10, Rappaport Chapter 5
# ─────────────────────────────────────────────────────────────────────────────

# RMS Delay Spread per environment type (in nanoseconds)
RMS_DELAY_SPREAD_NS: Dict[EnvironmentType, float] = {
    EnvironmentType.FREE_SPACE:        0.0,
    EnvironmentType.OPEN_OFFICE:       35.0,
    EnvironmentType.INDOOR_OFFICE:     50.0,
    EnvironmentType.WAREHOUSE:         100.0,
    EnvironmentType.CONCRETE_BUILDING: 150.0,
    EnvironmentType.CORRIDOR:          30.0,
}
"""RMS delay spread in nanoseconds. Source: ITU-R P.1238-10 Table 4."""

# Default Rician K-factor in dB for LOS environments
DEFAULT_RICIAN_K_FACTOR_DB: float = 6.0
"""Rician K-factor for LOS paths: 6 dB (typical indoor LOS).
   Higher K means stronger direct path relative to scattered components."""

# Default reference distance for path loss models
DEFAULT_REFERENCE_DISTANCE_M: float = 1.0
"""Reference distance d0 for the Log-Distance Path Loss model."""


# ─────────────────────────────────────────────────────────────────────────────
# Interference Type Definitions
# ─────────────────────────────────────────────────────────────────────────────

class InterferenceType(Enum):
    """Non-WiFi and WiFi interference source classifications."""
    NONE = "none"
    BLUETOOTH = "bluetooth"
    MICROWAVE = "microwave"
    ZIGBEE = "zigbee"
    NEIGHBOR_AP = "neighbor_ap"
    ADJACENT_CHANNEL = "adjacent_channel"
    HIDDEN_NODE = "hidden_node"
    RADAR = "radar"


# ─────────────────────────────────────────────────────────────────────────────
# BSS Coloring / Spatial Reuse
# Source: IEEE 802.11ax-2021 Section 26.10
# ─────────────────────────────────────────────────────────────────────────────

OBSS_PD_MIN_DBM: float = -82.0
"""OBSS-PD lower bound: -82 dBm (most conservative, always defer)."""

OBSS_PD_MAX_DBM: float = -62.0
"""OBSS-PD upper bound: -62 dBm (most aggressive spatial reuse)."""

BSS_COLOR_RANGE: Tuple[int, int] = (1, 63)
"""BSS Color identifier range: 1 to 63 (6 bits)."""


# ─────────────────────────────────────────────────────────────────────────────
# Application QoE Weights
# ─────────────────────────────────────────────────────────────────────────────

class ApplicationType(Enum):
    """Client application types affecting QoE weighting."""
    VOICE = "voice"
    VIDEO = "video"
    BROWSING = "browsing"
    GAMING = "gaming"
    BULK_DOWNLOAD = "bulk_download"


# (latency_weight, throughput_weight, loss_weight, jitter_weight, retry_weight)
QOE_APP_WEIGHTS: Dict[ApplicationType, Tuple[float, float, float, float, float]] = {
    ApplicationType.VOICE:         (0.40, 0.10, 0.20, 0.25, 0.05),
    ApplicationType.VIDEO:         (0.25, 0.35, 0.20, 0.10, 0.10),
    ApplicationType.BROWSING:      (0.15, 0.40, 0.15, 0.05, 0.25),
    ApplicationType.GAMING:        (0.45, 0.15, 0.20, 0.15, 0.05),
    ApplicationType.BULK_DOWNLOAD: (0.05, 0.55, 0.15, 0.05, 0.20),
}
"""Per-application-type weights for QoE computation.
   Order: (latency, throughput, packet_loss, jitter, retry_rate)."""


# ─────────────────────────────────────────────────────────────────────────────
# Health Index Weights (Client-Centric)
# ─────────────────────────────────────────────────────────────────────────────

HEALTH_INDEX_WEIGHTS: Dict[str, float] = {
    "client_experience": 0.40,
    "rf_health": 0.20,
    "capacity_health": 0.15,
    "interference_health": 0.15,
    "mobility_health": 0.10,
}
"""Weights for aggregating individual health indices into overall AP Health.
   Client experience carries the highest weight per Arista client-centric philosophy."""

AP_HEALTH_MEAN_WEIGHT: float = 0.6
"""Weight given to mean of client health scores in AP health aggregation."""

AP_HEALTH_WORST_CLIENT_WEIGHT: float = 0.4
"""Weight given to worst-performing client in AP health aggregation.
   Ensures worst-case client drives RRM optimization."""


# ─────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────────────

def dbm_to_mw(dbm: float) -> float:
    """Convert power from dBm to milliwatts.
    Formula: mW = 10^(dBm / 10)"""
    return 10.0 ** (dbm / 10.0)


def mw_to_dbm(mw: float) -> float:
    """Convert power from milliwatts to dBm.
    Formula: dBm = 10 * log10(mW)"""
    if mw <= 0:
        return -150.0  # Practical floor
    return 10.0 * math.log10(mw)


def db_to_linear(db: float) -> float:
    """Convert dB to linear ratio.
    Formula: linear = 10^(dB / 10)"""
    return 10.0 ** (db / 10.0)


def linear_to_db(linear: float) -> float:
    """Convert linear ratio to dB.
    Formula: dB = 10 * log10(linear)"""
    if linear <= 0:
        return -150.0
    return 10.0 * math.log10(linear)


def freq_mhz_to_hz(freq_mhz: float) -> float:
    """Convert frequency from MHz to Hz."""
    return freq_mhz * 1e6


def wavelength_m(freq_hz: float) -> float:
    """Compute wavelength in meters for a given frequency in Hz.
    Formula: λ = c / f"""
    return SPEED_OF_LIGHT_MPS / freq_hz
