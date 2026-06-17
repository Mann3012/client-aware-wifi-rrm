# Team Onboarding: WiFi Radio Resource Management (RRM) Prototype

Welcome to the team! This document is designed to get you up to speed on the project. It assumes you are a software engineer who knows Python but has no prior experience with WiFi networking or wireless systems.

---

## Project Goal

The goal of this project is to build and evaluate a closed-loop controller that optimizes WiFi Access Point (AP) settings in real time. 

By analyzing signal metrics and detecting anomalies (such as microwave oven interference, bluetooth congestions, or client spikes), the system recommends optimizations (like changing channels, reducing width, or adjusting power) to improve client Quality of Experience (QoE) and prevent dropouts.

---

## WiFi Networking Basics for Software Engineers

If you have never worked with wireless networks, here are the key concepts explained in software terms:

### 1. The Physical Layer (PHY)
* **Access Point (AP)**: The wireless host. Think of it as a web server that communicates over radio frequencies instead of ethernet cables.
* **Client**: The wireless node (e.g., your laptop). Think of it as the client browser.
* **Channel**: A specific frequency band. Think of it as a port number. Wireless communication can only occur if the client and AP are tuned to the same channel. Multiple APs on the same channel cause packet collisions (like port conflicts).
* **RSSI**: Received Signal Strength Indicator (measured in dBm, e.g., `-30` to `-95`). This indicates signal strength. Values closer to zero are stronger. A signal of `-50dBm` is strong; `-80dBm` is weak and prone to errors.
* **Noise Floor**: Background electromagnetic noise (measured in dBm, e.g., `-90` to `-105`). It represents background static. Microwave ovens and Bluetooth devices generate noise, raising the noise floor (e.g., from `-95` to `-80` dBm).
* **SNR**: Signal-to-Noise Ratio (measured in dB). Formula: $\text{RSSI} - \text{Noise Floor}$. If SNR is high ($>25\text{dB}$), signals are clear. If SNR is low ($<15\text{dB}$), background noise drowns out the transmission, leading to corruption.

### 2. The Media Access Control Layer (MAC)
* **Airtime Utilization**: WiFi is half-duplex; only one device can transmit on a channel at a time. Airtime utilization is the percentage of time the channel is busy. If utilization is high ($>70\%$), packets are queued, causing latency.
* **Retry Rate**: The fraction of packets that had to be retransmitted because they were not acknowledged. High retry rates ($>15\%$) occur when packets collide or get corrupted by noise, reducing throughput.

### 3. Management Layer
* **QoE (Quality of Experience)**: An aggregated metric indicating user experience, calculated using signal quality, retry rates, and congestion.
* **RRM (Radio Resource Management)**: The control logic. It monitors metrics and adjusts AP settings (channels, widths, power) to optimize network performance.

---

## Current Project Status

### Pre-Midterm Deliverables (Completed)
* **Dual-Mode Simulator**: Synthetic and physics-based telemetry models.
* **FastAPI Backend Services**: REST endpoints for telemetry, alerts, and recommendations.
* **SQLite Persistence**: Schema creation and historical data seeding (6 hours of telemetry on startup).
* **Change Detection Engine**: EWMA spike detection and CUSUM shift detection.
* **RRM Policy Engine**: Rule-based engine that recommends adjustments and updates simulator states.
* **Interactive Streamlit Web Dashboard**: Live scorecard, trend charts, alert lists, and manual controls.
* **Integration Tests**: Tests verifying schema transactions, anomaly alerts, and recommendations.

### Mid-Term Deliverables (In Progress / Next Steps)
* **Bayesian Optimizer**: Tuning detection and policy thresholds to maximize network QoE.
* **Interference Classifier**: An ML model to classify interference sources from metric signatures.
* **Client Steering Logic**: Triggers to hand off clients with weak signals to stronger adjacent APs.

### End-Term Deliverables (Planned Roadmap)
* **Safe Reinforcement Learning**: An RL agent for channel adjustments, constrained by safety guardrails.
* **Graph Neural Network (GNN)**: Multi-AP cooperative channel allocation using graph-modeled topologies.

---

## Code Reading Order

To understand how the codebase works, we recommend reading files in the following order:

```
run.py (Entry point & process manager)
  │
  └──> src/database/models.py (Database tables schema)
        │
        └──> src/realistic_simulator/telemetry_simulator.py (Physics-based metric generation)
              │
              └──> src/simulator/generator.py (Background simulator execution worker)
                    │
                    └──> src/analytics/change_detection.py (EWMA/CUSUM anomaly logic)
                          │
                          └──> src/analytics/policy_engine.py (RRM rules logic)
                                │
                                └──> src/api/routes.py (REST API endpoint declarations)
                                      │
                                      └──> dashboard/app.py (Streamlit dashboard frontend)
```

1. **[run.py](file:///c:/Users/l/Desktop/Artista/run.py)**: Start here to see how the FastAPI and Streamlit processes are initialized and monitored.
2. **[src/database/models.py](file:///c:/Users/l/Desktop/Artista/src/database/models.py)**: Check the definitions of the telemetry, alert, and recommendation tables.
3. **[src/realistic_simulator/telemetry_simulator.py](file:///c:/Users/l/Desktop/Artista/src/realistic_simulator/telemetry_simulator.py)**: Review the physics-based formulas used to calculate RSSI, SNR, Airtime, and Retry Rates.
4. **[src/simulator/generator.py](file:///c:/Users/l/Desktop/Artista/src/simulator/generator.py)**: Examine how the background worker updates AP states, runs calculations, triggers alerts, and evaluates policies.
5. **[src/analytics/change_detection.py](file:///c:/Users/l/Desktop/Artista/src/analytics/change_detection.py)**: Analyze how EWMA and CUSUM check for metrics anomalies.
6. **[src/analytics/policy_engine.py](file:///c:/Users/l/Desktop/Artista/src/analytics/policy_engine.py)**: Review the rules that map telemetry states and active alerts to recommended adjustments.
7. **[src/api/routes.py](file:///c:/Users/l/Desktop/Artista/src/api/routes.py)**: See how data is retrieved from the database and served to client requests.
8. **[dashboard/app.py](file:///c:/Users/l/Desktop/Artista/dashboard/app.py)**: Understand how the Streamlit frontend visualizes data and coordinates controls.

---

## Important Files Reference

| File Path | Description | Why It Matters |
| :--- | :--- | :--- |
| **[run.py](file:///c:/Users/l/Desktop/Artista/run.py)** | Process manager | Serves as the single execution command for local development. |
| **[src/database/models.py](file:///c:/Users/l/Desktop/Artista/src/database/models.py)** | Database tables | Defines the schema for persistent network logs. |
| **[src/simulator/generator.py](file:///c:/Users/l/Desktop/Artista/src/simulator/generator.py)** | Simulation manager | Runs the background simulation loop and orchestrates analytics. |
| **[src/realistic_simulator/telemetry_simulator.py](file:///c:/Users/l/Desktop/Artista/src/realistic_simulator/telemetry_simulator.py)** | Physics engine | Implements standard network path loss and capacity equations. |
| **[src/analytics/change_detection.py](file:///c:/Users/l/Desktop/Artista/src/analytics/change_detection.py)** | Anomaly engine | Detects metric shifts (CUSUM) and spikes (EWMA). |
| **[src/analytics/policy_engine.py](file:///c:/Users/l/Desktop/Artista/src/analytics/policy_engine.py)** | Decision maker | Evaluates states and triggers optimizations like channel changes. |
| **[dashboard/app.py](file:///c:/Users/l/Desktop/Artista/dashboard/app.py)** | Streamlit frontend | Serves as the interactive web console. |
| **[tests/validation.py](file:///c:/Users/l/Desktop/Artista/tests/validation.py)** | Integration tests | Verifies database operations, alerts, and policies. |

---

## Development Workflow

Follow these guidelines to modify and test code safely:

### 1. Running Integration Tests
Before making changes, verify the current build:
```powershell
python tests/validation.py
python tests/validation_realistic.py
```
Ensure all tests pass.

### 2. Modifying Analytics or Policies
* If you edit **[change_detection.py](file:///c:/Users/l/Desktop/Artista/src/analytics/change_detection.py)** or **[policy_engine.py](file:///c:/Users/l/Desktop/Artista/src/analytics/policy_engine.py)**, add corresponding test assertions in **[tests/validation.py](file:///c:/Users/l/Desktop/Artista/tests/validation.py)**.
* Run tests to confirm the new logic functions correctly and does not break existing features.

### 3. Modifying Database Models
* If you add columns to **[src/database/models.py](file:///c:/Users/l/Desktop/Artista/src/database/models.py)**, update the corresponding Pydantic schemas in **[src/api/schemas.py](file:///c:/Users/l/Desktop/Artista/src/api/schemas.py)** so the new fields are serialized correctly.
* Delete the old local database `rrm_database.db` so the schema updates on the next startup:
  ```powershell
  Remove-Item .\rrm_database.db -ErrorAction SilentlyContinue
  ```

---

## Common Mistakes to Avoid

* **Running Scripts Individually**: Do not start `src/api/main.py` directly without configuring PYTHONPATH. Always use `python run.py`, which configures paths and starts both services.
* **Failing to Clear SQLite Database**: If database tables change, SQLite will not auto-migrate existing files, causing schema mismatches. Delete `rrm_database.db` so it recreates on boot.
* **Adding Unused Imports**: The generator parses imports dynamically for dependency management. Keep imports clean and remove unused packages.
* **Wrong Units**: In the realistic simulator, airtime utilization is calculated from `0` to `100` internally, but is stored in the database as a fraction (`0.0` to `1.0`) to remain consistent with standard metrics. Remember to scale values appropriately.

---

## FAQ

#### Q: How do I change the time-step of the simulation?
A: Open `.env` and change `SIMULATOR_INTERVAL_SECONDS`. To speed up simulation, set `SIMULATOR_SPEED_MULTIPLIER` to values higher than `1.0` (e.g., `5.0`).

#### Q: Can I run this prototype against my actual laptop WiFi?
A: Yes! On Windows, set `SIMULATOR_MODE=legacy` and `SEED_HISTORICAL_DATA=false` in `.env`. The simulator will scrape your laptop's live adapter metrics using `netsh wlan` and write them to the telemetry table as `AP_001_Floor1`.

#### Q: Why is there an `N/A` value in the QoE category on the dashboard?
A: Make sure `.env` has `SIMULATOR_MODE=realistic`. The legacy mode does not calculate QoE scores.

#### Q: How do I verify a new recommendation rule?
A: You can force condition values in `tests/validation.py` and run the test suite, or use the **Trigger Simulation Minute** button on the dashboard to step metrics manually and monitor the alerts logs.
