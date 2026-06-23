# Realistic Wi-Fi Telemetry Simulator - Network Model

This document outlines the theoretical networking model and formula-driven causal pipeline implemented in the realistic telemetry simulator.

## 1. Causal Physics Pipeline

The simulator operates on a deterministic causal chain where physical environment variables flow downwards to compute logical network performance:

`Client Mobility` ➔ `Distance` ➔ `Log-Distance Path Loss` ➔ `RSSI` ➔ `Noise Floor` ➔ `SNR` ➔ `Retry Rate` ➔ `QoE` ➔ `Recommendations`

By replacing randomized variables with this deterministic chain, the simulation accurately mimics a digital twin of an indoor Wi-Fi network.

---

## 2. Floor Plan & Mobility Model

### Client Mobility (Random Walk)
- **Formula:** `client.x += U(-1, 1)`, `client.y += U(-1, 1)`
- **Variables:** `U` is a uniform random distribution.
- **Assumptions:** Clients drift randomly by up to 1 meter per simulation tick to simulate human movement in an office space.

### Distance Calculation
- **Formula:** `d = √((x₂ − x₁)² + (y₂ − y₁)²)`
- **Units:** Meters (m)
- **Assumptions:** Pure Euclidean distance in 2D space. Elevation is not currently factored into the primary distance model.

---

## 3. Propagation & Signal Model

### Log-Distance Path Loss Model
- **Formula:** `PL(d) = PL(d0) + 10 * n * log10(d / d0)`
- **Variables:**
  - `d` = Distance from AP to client in meters.
  - `d0` = Reference distance (1.0 meter).
  - `n` = Path Loss Exponent. Set to **3.0** (standard for indoor office environments).
  - `PL(d0)` = Free Space Path Loss at 1 meter.

### Reference Distance Path Loss (FSPL)
- **Formula:** `PL(d0) = 32.44 + 20*log10(d0_km) + 20*log10(freq_MHz)`
- **Source:** Free Space Path Loss derivation.
- **Assumptions:** FSPL is strictly used to anchor the starting path loss at 1 meter.

### Received Signal Strength Indicator (RSSI)
- **Formula:** `RSSI = TxPower - PL(d) - WallLoss`
- **Variables:**
  - `WallLoss` = `WallCount * WallAttenuation`
  - `WallAttenuation` = 3.0 dB (approximating standard drywall).
- **Units:** Decibel-milliwatts (dBm).

---

## 4. MAC Layer & Interference Model

### Noise Floor
- **Formula:** `NoiseFloor = BaseNoise + InterferenceContribution`
- **Variables:** `BaseNoise` is anchored at -95 dBm. `InterferenceContribution` relies on scenario-driven interference bursts (e.g., Microwave generating +15 dB).
- **Units:** dBm.

### Signal-to-Noise Ratio (SNR)
- **Formula:** `SNR = RSSI - NoiseFloor`
- **Source:** CWNA Wireless Design Guidelines.
- **Units:** Decibels (dB).

### Packet Retry Rate
- **Formula:** `RetryRate = min(80, max(1, 100 * e^(-0.12 * SNR)))`
- **Source:** 802.11 physical layer retransmission approximations.
- **Behavior:** This creates an exponential decay curve. An SNR of 35 dB produces ~1% retries, while an SNR of 10 dB produces ~30% retries.
- **Units:** Percentage (%).

### Airtime Utilization
- **Formula:** `Airtime = min(100, (TotalClientDemand / ChannelCapacity) * 100)`
- **Variables:** `ChannelCapacity` is approximated (e.g., 300 Mbps for a 2x2 802.11ac 40MHz channel). `TotalClientDemand` sums the mbps demanded by active clients.

---

## 5. Quality of Experience (QoE) & RRM Engine

### Quality of Experience (QoE) Model
- **Formula:** `QoE = (0.40 * SNRScore) + (0.30 * RetryScore) + (0.20 * NoiseScore) + (0.10 * ClientLoadScore)`
- **Variables:** 
  - Each metric score is normalized to a 0-100 scale.
  - QoE represents an engineering heuristic mapping physical Layer 1/2 performance to expected User Experience.

### Radio Resource Management (RRM) Recommendation Engine
- **Behavior:** Scans normalized telemetry metrics and explicit active events to generate a **ranked array** of mitigation actions.
- **Example Rules:**
  - `SNR < 25` & `Interference Active` ➔ `CHANNEL_CHANGE`
  - `Distance > 20m` & `SNR < 20` ➔ `POWER_INCREASE`
- **Output Structure:** `[{"action": "...", "confidence": 0.91, "expected_qoe_gain": 18.0}]`
