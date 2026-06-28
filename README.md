# AI-Assisted Client-Aware WiFi Radio Resource Management (RRM) System

A real-time **Digital Twin** prototype that simulates WiFi Access Point telemetry using physics-backed networking formulas, evaluates network quality, detects anomalies using statistical analytics (EWMA & CUSUM), and recommends Radio Resource Management optimizations with ranked confidence scoring and root cause traceability.

---

## Project Overview

### What Problem the Project Solves
In modern wireless networking, WiFi environments are dynamic, unpredictable, and vulnerable to various forms of interference (e.g., microwaves, Bluetooth devices, and overlapping neighbor Access Points). Traditional Radio Resource Management (RRM) algorithms often rely on static heuristics or vendor-specific closed-loop control that fails to account for client-side experiences and localized anomalies in real time. 

This project solves this by creating a **client-aware WiFi RRM Digital Twin** that:
* Simulates realistic indoor WiFi physics using the **Log-Distance Path Loss Model** and capacity-based airtime calculations.
* Runs explicit, repeatable **network scenarios** (Microwave Burst, Bluetooth Storm, Crowded Conference Room, etc.) with deterministic causal chains.
* Integrates client-side Quality of Experience (QoE) metrics into RRM decisions.
* Uses real-time statistical change detection (EWMA and CUSUM) to identify sudden metric spikes and persistent environmental noise.
* Generates **ranked, explainable recommendations** with confidence scores, root cause labels, and expected QoE gains.

### Why the Project Exists
This prototype was developed to demonstrate a closed-loop, data-driven WiFi optimization architecture. It serves as a testing ground for comparing physics-backed network simulators, statistical anomaly detection engines, and RRM optimization policies before deploying them to enterprise wireless hardware.

### Current Project Status
The prototype is **fully operational** as a Digital Twin simulator. It features:
1. A FastAPI backend server managing a background telemetry simulator with a **Scenario Engine** that cycles through 6 predefined network scenarios.
2. A SQLite database (SQLAlchemy ORM) storing telemetry, alerts, ranked recommendations, and scenario event logs.
3. A premium Streamlit dashboard with **Scenario Timeline**, **Root Cause Analysis Panel**, **Topology Visualization**, and **Manual Scenario Selector**.
4. Three simulation modes: **Demo** (auto-cycles scenarios every 30s), **Auto** (random scenarios), and **Manual** (API-driven scenario selection).
5. Physics validation tests verifying formula correctness (SNR = RSSI − Noise, RSSI drops with distance, etc.).

### Mid-Term Goals
* **Bayesian Optimization**: Integrate a Bayesian optimizer to dynamically tune RRM thresholds (e.g., RSSI, SNR, and Noise Floor limits) based on cumulative network QoE.
* **Interference Classification**: Implement a lightweight machine learning classifier (e.g., Random Forest) to identify the specific source of interference (Microwave, BLE, or Neighbor AP) based on high-frequency telemetry features.
* **Client Steering Heuristics**: Expand recommendations to include client steering (band steering or AP-to-AP handoff triggers).

### End-Term Goals
* **Deep Reinforcement Learning (RL) / Safe RL**: Deploy a Q-learning or PPO agent to manage channel and power allocations, wrapped with safety guardrails to prevent packet loss.
* **Graph Neural Networks (GNNs)**: Model the multi-AP network topology as a graph to perform joint cooperative RRM optimization across multiple adjacent cells.

---

## WiFi Networking Concepts

* **Access Point (AP)**: A hardware device that allows wireless devices (clients) to connect to a wired network. Example: The ceiling-mounted router in an office.
* **Client**: Any device (phone, laptop, IoT sensor) connected to an AP to access network services.
* **Channel**: A specific frequency range allocated for wireless communications. For example, 2.4GHz uses channels 1, 6, and 11, while 5GHz uses channels like 36, 40, and 149.
* **RSSI (Received Signal Strength Indicator)**: A measurement of the power present in a received radio signal, represented in decibels relative to one milliwatt (dBm). It is a negative value; closer to 0 means a stronger signal. Example: `-40 dBm` is excellent, while `-80 dBm` is very weak.
* **Noise Floor**: The measure of the signal strength of all background noise and unwanted signals in the environment, represented in dBm. Example: `-95 dBm` is clean, while `-80 dBm` indicates severe environmental noise/interference.
* **SNR (Signal-to-Noise Ratio)**: The difference between the signal strength (RSSI) and the noise floor, measured in decibels (dB). High SNR means clear signals. Formula: `SNR = RSSI - Noise Floor`. Example: If RSSI is `-65 dBm` and Noise Floor is `-95 dBm`, SNR is `30 dB` (excellent).
* **Retry Rate**: The percentage of transmitted packets that failed to be acknowledged on the first attempt and had to be retransmitted, expressed as a fraction from `0.0` to `1.0`. High retry rates indicate packet collisions or signal degradation. Example: `0.02` (2%) is normal, whereas `0.25` (25%) indicates significant congestion or interference.
* **Airtime Utilization**: The percentage of time that the wireless medium (channel) is occupied by transmissions, expressed from `0.0` to `1.0` (or 0% to 100%). Wireless is a shared medium; if airtime utilization is high, clients must wait longer to transmit. Example: `0.15` (15%) is idle, while `0.80` (80%) is highly congested.
* **Interference**: Unwanted electromagnetic signals that disrupt wireless communications. It can be *co-channel* (other APs sharing the channel) or *non-WiFi* (microwave ovens, baby monitors, BLE devices).
* **QoE (Quality of Experience)**: A subjective/objective metric assessing the user's overall satisfaction with the network service, represented as a score (0 to 100). It is calculated dynamically based on latency-impacting metrics like retry rates, low SNR, and airtime congestion.
* **RRM (Radio Resource Management)**: System-level control algorithms that dynamically adjust AP radio parameters (such as channel, transmit power, and channel width) to optimize overall network capacity and user experience.

---

## Current Features

* **Digital Twin Scenario Engine**: Cycles through 6 predefined network scenarios (Normal Office, Microwave Burst, Bluetooth Storm, Neighbor AP Congestion, Crowded Conference Room, Weak Signal Corner) with deterministic causal chains.
* **Three Simulation Modes**:
  * **Demo Mode** (default): Auto-cycles through all 6 scenarios every 30 seconds — ideal for live demonstrations.
  * **Auto Mode**: Randomly selects a new scenario after each duration expires.
  * **Manual Mode**: Scenarios are set via API or dashboard dropdown — useful during judging.
* **Physics-Backed Telemetry**: Uses Log-Distance Path Loss, capacity-based airtime, exponential retry rate, and weighted QoE scoring.
* **Ranked Recommendations**: Each recommendation includes `action`, `confidence`, `root_cause`, `expected_qoe_gain`, and a multiline causal chain explanation.
* **Scenario Event Log**: Tracks every scenario transition with start/end times, root cause, and recommendation triggered — enabling a visual timeline.
* **Root Cause Analysis Panel**: Dashboard panel showing the full causal chain from scenario → noise → SNR → retry → QoE → recommendation.
* **Topology Visualization**: Displays AP and client positions on a scatter plot, updated per scenario transition.
* **Statistical Change Detection Engine**: Uses EWMA to catch instant spikes in retry rates and airtime, and CUSUM to detect small persistent shifts in the noise floor.
* **Sensing Radio & Additional Radio Panel**: Decodes real-time `spectrum_snapshot` payloads to render:
  * **FFT Spectrum Sweep**: Live line chart showing frequency bins (MHz) vs power (dBm) to inspect spectral interference characteristics.
  * **Channel Quality score**: A dynamic 0-100 metric calculated based on noise level, busy time, and active interferers.
  * **Detected Interferers**: Real-time identification of non-WiFi (Bluetooth/Microwave) or overlapping neighbor AP interferers including center frequency, bandwidth, power, and confidence.
* **Pure API Presentation Layer (Dashboard Refactor)**: Removed all physics equations (`compute_path_loss`, `estimate_post_action_impact`, and math formulas) from the dashboard layer to enforce clean UI separation.
* **Single Immutable Snapshot & Scenario Locking**: Restructured rendering to query API endpoints exactly once per cycle and freeze the active scenario name globally, preventing rendering inconsistency across tabs when the background simulator ticks.
* **Closed-Loop Policy Engine**: Evaluates active anomalies and telemetry values to issue RRM recommendations, applying channel changes back to the simulator.
* **Interactive Streamlit Dashboard**: Renders live scorecards, multi-metric charts, scenario timeline, alert logs, and recommendation interface.
* **Manual Scenario Selector**: Dropdown in the dashboard to instantly force any scenario on any AP — no waiting required.
* **Manual Simulation Step**: Button to force an immediate simulation tick from the dashboard during presentations.

---

## Folder Structure

```
Artista/
├── .env.example                     # Environment configuration template
├── change_detection.py              # Standalone change detection test/demo script
├── rrm_database.db                  # Main SQLite database (auto-generated)
├── run.py                           # Project bootstrap script (FastAPI + Streamlit)
├── requirements.txt                 # Project dependencies
├── telemetry_output.csv             # Legacy simulator CSV output (if run standalone)
├── telemetry_simulator.py           # Legacy simulator standalone script and tests
├── update_dashboard.py              # Utility script to patch the dashboard code
├── update_generator.py              # Utility script to patch the simulator code
│
├── dashboard/
│   └── app.py                       # Streamlit dashboard (Timeline, Topology, Root Cause)
│
├── src/
│   ├── __init__.py                  # Root package initializer
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── change_detection.py      # EWMA and CUSUM analytical detectors
│   │   └── policy_engine.py         # Rule-based RRM policy evaluator
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI application setup and lifespan control
│   │   ├── routes.py                # REST API endpoints, scenario control, & manual triggers
│   │   └── schemas.py               # Pydantic schemas for data serialization
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py            # SQLAlchemy engine, session maker, and migrations
│   │   └── models.py                # SQLAlchemy DB models (Telemetry, Alert, Recommendation, ScenarioEvent)
│   │
│   ├── realistic_simulator/
│   │   ├── models.py                # Dataclasses (APState, ClientState, QoE, InterferenceEvent, TelemetryRecord)
│   │   ├── recommendation_engine.py # Ranked recommendation engine with causal heuristics
│   │   ├── scenario_engine.py       # Scenario definitions and transition logic
│   │   └── telemetry_simulator.py   # Physics engine (path loss, SNR, retry rate, QoE)
│   │
│   └── simulator/
│       ├── __init__.py
│       └── generator.py             # Background orchestrator (scenario transitions, DB writes)
│
└── tests/
    ├── test_simulator.py            # Physics formula validation tests
    ├── validation.py                # Integration checks for database, analytics, and rules
    └── validation_realistic.py      # Realistic telemetry + change detection assertions
```

### Key Subdirectory Purposes
* **`dashboard/`**: Contains the Streamlit UI. Communicates with the backend via REST API. Includes Scenario Timeline, Root Cause Analysis, and Topology Visualization panels.
* **`src/analytics/`**: Houses the statistical detection intelligence (EWMA for spikes, CUSUM for shifts) and the rule-based policy engine.
* **`src/api/`**: Serves as the system interface layer. Provides REST endpoints for telemetry, alerts, recommendations, scenario history, and manual scenario control.
* **`src/database/`**: Defines the persistence layer with SQLAlchemy models for `telemetry`, `alerts`, `recommendations`, and `scenario_events` tables.
* **`src/realistic_simulator/`**: Contains the physics engine (Log-Distance Path Loss, capacity-based airtime, exponential retry rate), the Scenario Engine (6 scenarios), and the Recommendation Engine (ranked output).
* **`src/simulator/`**: Manages the background simulation loop, scenario transitions, and database commits.
* **`tests/`**: Contains physics validation tests and integration verification scripts.

---

## Technology Stack

* **Backend**: FastAPI (Python) with Uvicorn ASGI server
* **Database**: SQLite (SQLAlchemy ORM)
* **Dashboard**: Streamlit (Python) with Plotly for topology visualization
* **Analytics**: Pandas, NumPy
* **Simulation**: Physics-backed Log-Distance Path Loss Model, capacity-based airtime utilization, exponential retry rate, and weighted QoE scoring
* **ML Components**: Currently rule-based and statistical heuristics (EWMA and CUSUM); structured to support Bayesian Optimization, classifiers, and RL agents in future iterations.

---

## Installation Guide (Windows)

Follow these steps to set up and run the project locally on Windows:

### 1. Clone Project
Clone the repository to your local directory:
```powershell
git clone <repository_url> Artista
cd Artista
```

### 2. Create Virtual Environment
Initialize a clean Python virtual environment:
```powershell
python -m venv venv
```

### 3. Activate Virtual Environment
Activate the environment in PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```
*(If you encounter a script execution policy error, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` first)*

### 4. Install Dependencies
Install all required packages:
```powershell
pip install -r requirements.txt
```

### 5. Verify Dependencies & Environments
Confirm all imports resolve correctly using Python:
```powershell
python -c "import fastapi; import uvicorn; import pydantic; import sqlalchemy; import pandas; import numpy; import plotly; import streamlit; import requests; import dotenv; print('All imports OK!')"
```

You can also list the installed packages inside the virtual environment:
```powershell
pip list
```
Ensure that `plotly` and `streamlit` are installed and match or exceed the minimum versions listed in `requirements.txt`.

### 6. Run the Test Suites (Verification)
Verify the simulator logic, database layers, policy engines, and analytics by running the regression test suite:
```powershell
# Run the formulas and recommendation engine checks
python tests/test_simulator.py

# Run database, alert, and integration checks
python tests/validation.py

# Run statistical analytics validation (EWMA & CUSUM)
python tests/validation_realistic.py
```
*Note: Make sure your `PYTHONPATH` includes the project root. If you see import errors, run: `$env:PYTHONPATH = (Get-Location).Path` beforehand.*

### 7. Configure Environment Variables
Copy the template `.env.example` file to create a `.env` file:
```powershell
copy .env.example .env
```

Key environment variables:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | *(empty, uses SQLite)* | Database connection string |
| `SIMULATOR_INTERVAL_SECONDS` | `60` | Seconds between simulation ticks |
| `SIMULATOR_SPEED_MULTIPLIER` | `1.0` | Speed multiplier for tick intervals |
| `NUMBER_OF_APS` | `3` | Number of Access Points to simulate |
| `SEED_HISTORICAL_DATA` | `true` | Seed historical data on first boot |
| `SEED_HOURS` | `6` | Hours of historical data to seed |
| `SIMULATOR_MODE` | `demo` | Simulation mode: `demo`, `auto`, or `manual` |
| `SIMULATOR_SCENARIO_DURATION_SECONDS` | `30` | How long each scenario lasts before transition |
| `API_HOST` | `127.0.0.1` | FastAPI server host |
| `API_PORT` | `8000` | FastAPI server port |

### 8. Run Application
Run the bootstrap orchestrator script:
```powershell
python run.py
```

### 9. Verify Setup
Once `run.py` runs, it will output:
* FastAPI backend documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* Streamlit Dashboard: [http://127.0.0.1:8501](http://127.0.0.1:8501)

Check if both links open successfully in your browser.

---

## How to Run

### run.py
The project is booted via `run.py`. This script:
1. Locates the Python executable and Streamlit binary inside the virtual environment (`venv` or `.venv`).
2. Spawns the **FastAPI Backend Process** using Uvicorn on port 8000.
3. Pauses for 4 seconds to allow database migration and initial startup tasks to complete.
4. Spawns the **Streamlit Dashboard Process** on port 8501.
5. Monitors both processes. If either server exits or crashes, `run.py` intercepts the exit, terminates the surviving process, and shuts down safely. Press `Ctrl+C` to cleanly exit both.

### Backend Startup & Database Initialization
When FastAPI starts:
1. The `lifespan` event handler inside `src/api/main.py` triggers.
2. It initializes the database schema by calling `init_db()`, generating tables if they do not exist.
3. It creates and starts the `BackgroundSimulator` thread (`SimulatorWorker` daemon thread).
4. The simulator defaults to **Demo mode**, automatically cycling through all 6 scenarios every 30 seconds.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root route — returns project info and available endpoints |
| `GET` | `/telemetry` | Fetch telemetry records (filterable by `ap_id`, `limit`) |
| `GET` | `/alerts` | Fetch anomaly alerts (filterable by `ap_id`, `active_only`, `limit`) |
| `GET` | `/recommendations` | Fetch RRM recommendations (filterable by `ap_id`, `limit`) |
| `GET` | `/ap-status` | Live health summary scorecard for all Access Points |
| `POST` | `/simulator/trigger` | Manually force a simulation step (useful for demos) |
| `GET` | `/scenario/history` | Fetch scenario event timeline (filterable by `ap_id`, `limit`) |
| `POST` | `/scenario/set` | Force a specific scenario on an AP (`ap_id`, `scenario_name`) |

Full interactive API documentation is available at `/docs` when the backend is running.

---

## Database Schema

The SQLite database schema is defined in `src/database/models.py`. It consists of four tables:

### 1. `telemetry` Table
Stores raw and calculated metric logs generated for each AP.
* `id` (Integer, PK): Unique row identifier.
* `timestamp` (DateTime, Indexed): UTC time when the telemetry was recorded.
* `ap_id` (String, Indexed): Identifies the Access Point (e.g., `AP_001_Floor1`).
* `channel` (Integer): Currently selected radio channel.
* `rssi` (Float): Average received signal strength of connected clients (dBm).
* `snr` (Float): Signal-to-noise ratio (dB).
* `noise_floor` (Float): Background noise floor level (dBm).
* `airtime_utilization` (Float): Channel occupancy ratio (0.0 to 1.0).
* `retry_rate` (Float): Retransmission rate (0.0 to 1.0).
* `client_count` (Integer): Count of active connected clients.
* `qoe_score` (Float, Nullable): Calculated quality of experience (0 to 100).
* `qoe_category` (String, Nullable): `Excellent`, `Good`, `Fair`, or `Poor`.
* `interference_type` (String, Nullable): Active interference source.
* `distance` (Float, Nullable): Average Euclidean distance to clients (meters).
* `max_distance` (Float, Nullable): Max client distance.
* `closest_client` (Float, Nullable): Min client distance.
* `furthest_client` (Float, Nullable): Max client distance (explicit).
* `freq_mhz` (Float, Nullable): AP operating frequency in MHz.
* `tx_power` (Float, Nullable): AP transmit power in dBm.
* `wall_count` (Integer, Nullable): Number of walls between AP and client.
* `wall_loss` (Float, Nullable): Obstacle attenuation in dB.
* `scenario_name` (String): Active scenario name (default: `Normal Office`).

### 2. `scenario_events` Table
Tracks explicit network scenario transitions and their outcomes.
* `id` (Integer, PK): Unique row identifier.
* `ap_id` (String, Indexed): Access Point ID.
* `start_time` (DateTime, Indexed): When the scenario started.
* `end_time` (DateTime, Nullable): When the scenario ended.
* `scenario_name` (String): Name of the scenario.
* `root_cause` (String, Nullable): Root cause label (e.g., `MICROWAVE`, `BLE`, `None`).
* `recommendation_triggered` (String, Nullable): Action triggered (e.g., `CHANNEL_CHANGE`).
* `client_topology_snapshot` (Text, Nullable): JSON snapshot of client positions at scenario start.

### 3. `alerts` Table
Stores anomalies flagged by the Change Detection Engine.
* `id` (Integer, PK): Unique row identifier.
* `timestamp` (DateTime, Indexed): Time the anomaly occurred.
* `ap_id` (String, Indexed): Affected Access Point ID.
* `alert_type` (String): Anomaly type (`retry_spike`, `airtime_congestion`, or `abnormal_interference`).
* `metric` (String): Violated metric name.
* `value` (Float): Observed metric value during the anomaly.
* `threshold` (Float): The computed statistical threshold that was crossed.
* `description` (String): Descriptive statistical explanation of the alert.

### 4. `recommendations` Table
Stores ranked optimization events suggested by the policy engine.
* `id` (Integer, PK): Unique row identifier.
* `timestamp` (DateTime, Indexed): Time recommendation was generated.
* `ap_id` (String, Indexed): Target Access Point ID.
* `action` (String): RRM action (`CHANNEL_CHANGE`, `LOAD_BALANCE`, `WIDTH_ADJUST`, `POWER_INCREASE`, `NONE`).
* `current_value` (String): Setting before optimization.
* `recommended_value` (String): Optimized target setting.
* `confidence` (Float): Confidence score (0.0 to 1.0).
* `root_cause` (String, Nullable): Explicit root cause label (e.g., `MICROWAVE_INTERFERENCE`, `CLIENT_CONGESTION`).
* `reason` (String): Multiline causal chain explanation.
* `expected_qoe_gain` (Float, Nullable): Expected QoE improvement if the action is taken.

---

## Scenario Engine

The Scenario Engine manages 6 predefined network scenarios, each producing a deterministic causal chain:

| Scenario | Noise Floor | Client Count | Key Effect | Expected Recommendation |
|---|---|---|---|---|
| **Normal Office** | −95 dBm | 2–8 | Clean baseline | `NONE` |
| **Microwave Burst** | −80 dBm (+15 dB) | Default | Heavy noise spike | `CHANNEL_CHANGE` |
| **Bluetooth Storm** | −90 dBm (+5 dB) | Default | Moderate noise + airtime | `CHANNEL_CHANGE` |
| **Neighbor AP Congestion** | −85 dBm (+10 dB) | Default | Noise + 25% airtime boost | `LOAD_BALANCE` |
| **Crowded Conference Room** | −95 dBm | 25–50 | High client density, 3× demand | `WIDTH_ADJUST` |
| **Weak Signal Corner** | −95 dBm | Default | Clients at 30m distance | `POWER_INCREASE` |

### Causal Chain Example (Microwave Burst)
```
Scenario: Microwave Burst
    ↓
Noise Floor: −95 → −80 dBm (+15 dB boost)
    ↓
SNR: 45 → 10 dB (drops because SNR = RSSI − Noise)
    ↓
Retry Rate: 1% → 30% (exponential: retry = min(80, max(1, 100 × e^(−0.12 × SNR))))
    ↓
QoE: 95 → 35 (penalties for low SNR, high retry rate)
    ↓
Recommendation: CHANNEL_CHANGE (confidence: 0.95, expected QoE gain: +20)
```

---

## Dashboard Guide

The dashboard is run via Streamlit. It contains:

### Header & Controls
* **AP Scorecard Grid**: Renders horizontal status cards for all APs. Cards change color dynamically:
  * **Healthy (Green)**: Active, no current alerts.
  * **Warning (Yellow)**: Non-critical alerts active (e.g., retry spike).
  * **Critical (Red)**: Critical alerts active (e.g., microwave interference).
* **Refresh Data Button**: Manually forces Streamlit to fetch fresh data from FastAPI endpoints.
* **Trigger Simulation Minute Button**: Forces a manual background simulator step.

### Sidebar — Manual Scenario Selector
* **AP Dropdown**: Select which Access Point to target.
* **Scenario Dropdown**: Choose from the 6 predefined scenarios.
* **Force Scenario Button**: Instantly applies the selected scenario — no waiting required. Ideal for live demos and judging.

### Tab 1: Live Telemetry & Trends
* **QoE & Active Events Scorecard**: Displays live QoE score, category, interference type, and active recommendation.
* **PHY / MAC Layer Metrics**: Airtime Utilization (%), Retry Rate (%), Noise Floor (dBm), Avg RSSI / SNR.
* **Metrics Over Time Charts**: Interactive line and bar charts showing historical trends.

### Tab 2: Alerts & Recommendations
* **Active Alerts Pane**: Lists the 5 most recent anomalies with severity tags:
  * `🔴 [HIGH]` for noise floor jumps.
  * `🟡 [MEDIUM]` for retry spikes.
  * `🔵 [LOW]` for airtime congestion.
* **Ranked Recommendations Table**: Displays action, confidence, root cause, expected QoE gain, and multiline causal chain explanation.

### Tab 3: Scenario Timeline & Topology
* **Scenario Timeline**: Chronological list of scenario events with start/end times, root cause, and recommendation triggered.
* **Root Cause Analysis Panel**: Shows the full causal chain for the current scenario.
* **Topology Visualization**: Plotly scatter plot showing AP position and connected client positions, updated per scenario transition.

---

## Simulator Physics

### Log-Distance Path Loss Model
Calculates client RSSI based on distance:
$$\text{PL}(d) = \text{PL}(d_0) + 10 \cdot n \cdot \log_{10}\left(\frac{d}{d_0}\right)$$
$$\text{RSSI}(d) = \text{Tx Power} - \text{PL}(d) - \text{Wall Loss}$$

Where:
* $d_0 = 1.0\text{m}$ (reference distance)
* $\text{PL}(d_0)$ computed via FSPL at reference distance
* $n = 3.0$ (path loss exponent for indoor office environment)
* Wall Loss = `wall_count × 3.0 dB` per wall

**Source**: Log-Distance Path Loss Model (indoor propagation literature). FSPL is used only to compute $\text{PL}(d_0)$ at the reference distance.

### Channel Capacity & Airtime
Maps channel width to capacity and computes airtime from demand:
```
Channel Width → Capacity: {20 MHz: 144 Mbps, 40 MHz: 300 Mbps, 80 MHz: 866 Mbps}
Airtime = (Total Client Demand / Channel Capacity) × 100
```

### Congestion-Aware Retry Rate
Calculates the combined retry rate from independent SNR (noise/interference) and airtime congestion probabilities:
$$\text{Retry}_{\text{SNR}} = \frac{\min\left(80.0, \max\left(1.0, 100.0 \times e^{-0.12 \times \text{SNR}}\right)\right)}{100.0}$$
$$\text{Retry}_{\text{congestion}} = 0.50 \times \left(\frac{\text{Airtime Utilization}}{100.0}\right) \times \left(1.0 - e^{-0.04 \times \text{Client Count}}\right)$$
$$\text{Retry}_{\text{combined}} = 1.0 - \left(1.0 - \text{Retry}_{\text{SNR}}\right) \times \left(1.0 - \text{Retry}_{\text{congestion}}\right)$$
$$\text{Retry}_{\text{final}} = \min\left(0.80, \max\left(0.01, \text{Retry}_{\text{combined}}\right)\right)$$

### QoE Calculation
Scores network quality on a scale of 0 to 100 as a weighted sum of four sub-scores:
$$\text{QoE} = 0.40 \cdot \text{SNRScore} + 0.30 \cdot \text{RetryScore} + 0.20 \cdot \text{NoiseScore} + 0.10 \cdot \text{ClientLoadScore}$$

Where the sub-scores are calculated as:
* **SNR Score**: $\text{SNRScore} = \min\left(100.0, \max\left(0.0, \frac{\text{SNR}}{35.0} \times 100.0\right)\right)$
* **Retry Score**: $\text{RetryScore} = \min\left(100.0, \max\left(0.0, 100.0 - (\text{Retry Rate} \times 100.0 \times 1.5)\right)\right)$
* **Noise Score**: $\text{NoiseScore} = \min\left(100.0, \max\left(0.0, 100.0 - (\max(0.0, \text{Noise Floor} - \text{Base Noise}) \times 5.0)\right)\right)$
* **Client Load Score**: $\text{ClientLoadScore} = \min\left(100.0, \max\left(0.0, 100.0 - \text{Airtime Utilization}\right)\right)$

---

## Analytics

The analytical layer detects shifts and spikes:

### EWMA (Exponentially Weighted Moving Average)
Used to identify quick spikes in high-frequency variables (Retry Rate and Airtime Utilization).
* **Formula**:
  $$S_t = \alpha Y_t + (1 - \alpha) S_{t-1}$$
  Where span $= 10$ and smoothing factor $\alpha = \frac{2}{\text{span} + 1} = 0.1818$.
* **Anomaly Condition**: Triggers if the current value is $> 3$ standard deviations above the moving average baseline. It filters high-frequency noise while catching sudden congestions.

### CUSUM (Cumulative Sum)
Used to detect small, persistent shifts in a metric's mean (Noise Floor levels).
* **Formula**:
  $$S_H(i) = \max(0, S_H(i-1) + Z(i) - K)$$
  Where $Z(i)$ is the standardized value relative to baseline mean/std, Drift parameter $K = 0.5$, and Decision Interval threshold $H = 5.0$.
* **Anomaly Condition**: Triggers when $S_H(i) > H$. This identifies persistent interference (like an active microwave or baby monitor) even if individual measurements fluctuate.

---

## Running Tests

Run the physics validation tests to verify all formulas:
```powershell
$env:PYTHONPATH = (Get-Location).Path; python tests/test_simulator.py
```

Expected output:
```
All formulas verified successfully.
```

The test verifies:
1. **SNR = RSSI − Noise Floor** (within 0.1 dB tolerance)
2. **RSSI drops with distance** (20m RSSI < 5m RSSI)
3. **QoE and Retry Rate respond to SNR** (low SNR → worse QoE and higher retry)
4. **Microwave Noise > Normal Noise** (scenario engine correctly applies interference)

---

## Troubleshooting

### Port Already in Use (FastAPI / Streamlit)
If port 8000 or 8501 is occupied, the application will fail to start.
* **Solution**: Identify and kill the process holding the port:
  ```powershell
  Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
  ```
  Or change the port values in your `.env` file before executing `python run.py`.

### Missing Dependencies
If you encounter `ModuleNotFoundError`:
* **Solution**: Ensure your virtual environment is active (indicated by `(venv)` prefix in terminal). Re-run dependency installation:
  ```powershell
  pip install -r requirements.txt
  ```

### Corrupted pip in Virtual Environment
If you see `ImportError: cannot import name '_log' from 'pip._internal.utils'`:
* **Solution**: Reinstall pip inside the venv:
  ```powershell
  python -m ensurepip --upgrade
  pip install --upgrade pip
  ```

### Database Recreation
If the database schema becomes corrupted or you wish to wipe metrics:
* **Solution**: Delete the database file. The system will recreate it and seed history on the next backend boot:
  ```powershell
  Remove-Item .\rrm_database.db -ErrorAction SilentlyContinue
  ```

### Dashboard Not Loading
If the browser shows "Connection Error" on port 8501:
* **Solution**: Check the console output of `run.py`. Ensure the FastAPI server is running on port 8000, as the Streamlit app relies on it to fetch metadata.

### N/A Values on Dashboard
If QoE or Interference fields show `N/A`:
* **Solution**: This occurs if the simulator is running in legacy mode. Change the mode in your `.env` file:
  ```env
  SIMULATOR_MODE=demo
  ```
  Then restart `run.py`.

---

## Future Work

### 1. Bayesian Optimization
Implement Bayesian Optimization (using `scikit-optimize` or `optuna`) to tune the parameters $K$, $H$ (CUSUM), and $\alpha$ (EWMA). The objective function will maximize average client QoE scores across the network while minimizing RRM channel change counts (to prevent thrashing).

### 2. ML-Based Interference Classification
Build a multi-class classification model. Input features will include standard deviations of noise floor, client SNR, and retry rates. Output labels will classify interference source:
$$\text{Class} \in \{\text{Clean}, \text{Microwave}, \text{BLE Congestion}, \text{Neighbor AP Interference}\}$$

### 3. Client Steering
Develop steering triggers. If client RSSI drop below `-75dBm` but adjacent APs report RSSI $>-65\text{dBm}$, issue handoff recommendations (`CLIENT_STEERING`).

### 4. Guardrails & Safe RL
Deploy Safe Reinforcement Learning. Implement mathematical bounds (e.g., minimum channel separation matrix and maximum transmit power caps) as hard constraints. The RL agent optimizes channels, but cannot violate boundaries, preventing network outages.

### 5. Graph Neural Networks (GNN)
Represent APs as nodes and channel overlaps as edge weights. Train a Graph Convolutional Network (GCN) to predict cooperative channel allocations, maximizing network-wide capacity.
