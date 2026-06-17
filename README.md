# AI-Assisted Client-Aware WiFi Radio Resource Management (RRM) System

A real-time prototype that simulates WiFi Access Point telemetry, evaluates network quality, detects anomalies using statistical analytics (EWMA & CUSUM), and recommends Radio Resource Management optimizations.

---

## Project Overview

### What Problem the Project Solves
In modern wireless networking, WiFi environments are dynamic, unpredictable, and vulnerable to various forms of interference (e.g., microwaves, Bluetooth devices, and overlapping neighbor Access Points). Traditional Radio Resource Management (RRM) algorithms often rely on static heuristics or vendor-specific closed-loop control that fails to account for client-side experiences and localized anomalies in real time. 

This project solves this by creating a **client-aware WiFi RRM prototype** that:
* Integrates client-side physics and Quality of Experience (Qoe) metrics into RRM decisions.
* Uses real-time statistical change detection (EWMA and CUSUM) to identify sudden metric spikes and persistent environmental noise.
* Automates channel, channel-width, and transmit power optimizations via an extensible rules-based policy engine.

### Why the Project Exists
This prototype was developed to demonstrate a closed-loop, data-driven WiFi optimization architecture. It serves as a testing ground for comparing physics-backed network simulators, statistical anomaly detection engines, and RRM optimization policies before deploying them to enterprise wireless hardware.

### Current Project Status
The prototype is **fully operational**. It features:
1. A FastAPI backend server that manages a background telemetry simulator, analytics engines, and database operations.
2. A SQLite database configured via SQLAlchemy that stores historical telemetry, alerts, and recommendations.
3. A premium Streamlit dashboard presenting real-time visual scorecards, trend charts, active alerts, and recommended RRM adjustments.
4. Two simulation modes: a legacy synthetic generator and a physics-backed realistic simulator.
5. Integration verification tests for both basic operations and realistic scenario validation.

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

* **Dual-Mode Telemetry Simulation**: Supports a legacy statistical generator and a realistic physics-backed simulator modeling signal path loss and channel capacity.
* **Continuous Background Telemetry Worker**: Runs in a daemon thread, generating minute-by-minute metrics for multiple APs.
* **Automatic Historical Seeding**: Seeds 6 hours of historical telemetry on initial startup if the database is empty, enabling immediate trend visualization.
* **Statistical Change Detection Engine**: Uses Exponentially Weighted Moving Averages (EWMA) to catch instant spikes in retry rates and airtime, and Cumulative Sum (CUSUM) to detect small, persistent shifts in the noise floor.
* **Closed-Loop Rule-Based Policy Engine**: Evaluates active anomalies and telemetry values to issue RRM recommendations, applying channel changes back to the simulator.
* **Interactive Streamlit Web Dashboard**: Renders live scorecards, multi-metric charts, alert logs, and a recommendation interface.
* **Manual Step Controller**: Allows users to manually force a simulation step from the UI.
* **Local Interface Querying**: Can optionally scrape local Windows adapter statistics using `netsh wlan` to inject actual host WiFi metrics into the database.

---

## Folder Structure

```
Artista/
├── .env.example                     # Environment configuration template
├── change_detection.py              # Standalone change detection test/demo script
├── rrm_database.db                  # Main SQLite database (auto-generated)
├── run.py                           # Project bootstrap script (fastapi + streamlit)
├── requirements.txt                 # Deduplicated project dependencies
├── telemetry_output.csv             # Legacy simulator CSV output (if run standalone)
├── telemetry_simulator.py           # Legacy simulator standalone script and tests
├── update_dashboard.py              # Utility script to patch the dashboard code
├── update_generator.py              # Utility script to patch the simulator code
│
├── dashboard/
│   └── app.py                       # Streamlit web application frontend
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
│   │   ├── routes.py                # REST API endpoints & manual simulation triggers
│   │   └── schemas.py               # Pydantic schemas for data serialization
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py            # SQLAlchemy engine, session maker, and migrations
│   │   └── models.py                # SQLAlchemy DB models (Telemetry, Alert, Recommendation)
│   │
│   ├── realistic_simulator/
│   │   ├── models.py                # Dataclasses for network states and records
│   │   ├── recommendation_engine.py # Physics-backed causal heuristic recommendations
│   │   └── telemetry_simulator.py   # Math-heavy physics equations for signal properties
│   │
│   └── simulator/
│       ├── __init__.py
│       └── generator.py             # Main background orchestrator thread
│
└── tests/
    ├── validation.py                # Integration checks for database, analytics, and rules
    └── validation_realistic.py      # Assertions checking realistic telemetry against detectors
```

### Key Subdirectory Purposes
* **`dashboard/`**: Contains the client user interface code. It communicates with the backend solely via REST API calls.
* **`src/analytics/`**: Houses the core processing intelligence (spikes, shifts, and decisions).
* **`src/api/`**: Serves as the system interface layer. Connects database operations and background state variables to HTTP client requests.
* **`src/database/`**: Defines the persistence layer, generating schemas and handling transaction sessions.
* **`src/realistic_simulator/`**: Contains the physics engine simulating path loss and capacities.
* **`src/simulator/`**: Manages backend processes, executing simulator intervals and committing results.
* **`tests/`**: Contains verification scripts.

---

## Technology Stack

* **Backend**: FastAPI (Python)
* **Database**: SQLite (SQLAlchemy ORM)
* **Dashboard**: Streamlit (Python)
* **Analytics**: Pandas, NumPy
* **Simulation**: Object-Oriented mathematical simulation of Log-Distance Path Loss and capacity physics.
* **ML Components**: Currently rule-based and statistical heuristics (EWMA and CUSUM); structured to support Bayesian Optimization, Scikit-Learn classifiers, and RL agents in future iterations.

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
Initialize a clean Python virtual environment named `venv` or `.venv`:
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

### 5. Configure Environment Variables
Copy the template `.env.example` file to create a `.env` file:
```powershell
copy .env.example .env
```
*(The default configuration falls back automatically to a local SQLite database file, sets up 3 Access Points, and seeds 6 hours of historical data.)*

### 6. Run Application
Run the bootstrap orchestrator script:
```powershell
python run.py
```

### 7. Verify Setup
Once `run.py` runs, it will output:
* FastAPI backend documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* Streamlit Dashboard: [http://127.0.0.1:8501](http://127.0.0.1:8501)
Check if both links open successfully in your browser.

---

## How to Run

### run.py
The project is booted via [run.py](file:///c:/Users/l/Desktop/Artista/run.py). This script:
1. Locates the Python executable and Streamlit binary inside the virtual environment (`venv` or `.venv`).
2. Spawns the **FastAPI Backend Process** using Uvicorn on port 8000.
3. Pauses for 4 seconds to allow database migration and initial startup tasks to complete.
4. Spawns the **Streamlit Dashboard Process** on port 8501.
5. Monitors both processes. If either server exits or crashes, `run.py` intercepts the exit, terminates the surviving process, and shuts down safely. Press `Ctrl+C` to cleanly exit both.

### Backend Startup & Database Initialization
When FastAPI starts:
1. The `lifespan` event handler inside [src/api/main.py](file:///c:/Users/l/Desktop/Artista/src/api/main.py) triggers.
2. It initializes the database schema by calling `init_db()` in [src/database/connection.py](file:///c:/Users/l/Desktop/Artista/src/database/connection.py), generating tables if they do not exist.
3. It creates and starts the `BackgroundSimulator` thread (`SimulatorWorker` daemon thread).
4. The worker check if `SEED_HISTORICAL_DATA` is enabled and the telemetry table is empty. If so, it seeds historical data step-by-step to populate databases before real-time cycles commence.

---

## Database Schema

The SQLite database schema is defined in [src/database/models.py](file:///c:/Users/l/Desktop/Artista/src/database/models.py). It consists of three tables:

### 1. `telemetry` Table
Stores raw and calculated metric logs generated for each AP.
* `id` (Integer, Primary Key): Unique row identifier.
* `timestamp` (DateTime, Indexed): UTC time when the telemetry was recorded.
* `ap_id` (String(50), Indexed): Identifies the Access Point (e.g., `AP_001_Floor1`).
* `channel` (Integer): Currently selected radio channel.
* `rssi` (Float): Average received signal strength of connected clients (dBm).
* `snr` (Float): Signal-to-noise ratio (dB).
* `noise_floor` (Float): Background noise floor level (dBm).
* `airtime_utilization` (Float): Channel occupancy ratio (from `0.0` to `1.0`).
* `retry_rate` (Float): Retransmission rate of data packets (from `0.0` to `1.0`).
* `client_count` (Integer): Count of active connected clients.
* `qoe_score` (Float, Nullable): Calculated quality of experience metric (0 to 100).
* `qoe_category` (String(50), Nullable): Category name: `Excellent`, `Good`, `Fair`, or `Poor`.
* `interference_type` (String(50), Nullable): Active external interference source: `None`, `Microwave`, `BLE Congestion`, or `Neighbor AP Congestion`.

### 2. `alerts` Table
Stores anomalies flagged by the Change Detection Engine.
* `id` (Integer, Primary Key): Unique row identifier.
* `timestamp` (DateTime, Indexed): Time the anomaly occurred.
* `ap_id` (String(50), Indexed): Affected Access Point ID.
* `alert_type` (String(50)): Anomaly type (`retry_spike`, `airtime_congestion`, or `abnormal_interference`).
* `metric` (String(50)): Violated metric name (`retry_rate`, `airtime_utilization`, or `noise_floor`).
* `value` (Float): Observed metric value during the anomaly.
* `threshold` (Float): The computed statistical threshold that was crossed.
* `description` (String(255)): Descriptive statistical explanation of the alert.

### 3. `recommendations` Table
Stores optimization events suggested by the policy engine.
* `id` (Integer, Primary Key): Unique row identifier.
* `timestamp` (DateTime, Indexed): Time recommendation was generated.
* `ap_id` (String(50), Indexed): Target Access Point ID.
* `action` (String(50)): RRM action (`CHANNEL_CHANGE`, `WIDTH_ADJUST`, `POWER_ADJUST`).
* `current_value` (String(50)): Setting before optimization (e.g., `"6"`, `"80MHz"`, `"14dBm"`).
* `recommended_value` (String(50)): Optimized target setting (e.g., `"11"`, `"20MHz"`, `"20dBm"`).
* `confidence` (Float): Confidence index of the policy match (0.0 to 1.0).
* `reason` (String(500)): Explanatory reason detailing the policy trigger.

---

## Dashboard Guide

The dashboard is run via Streamlit. It contains:

### Header & Controls
* **AP Scorecard Grid**: Renders horizontal status cards for all APs (`AP_001_Floor1`, `AP_002_Floor1`, `AP_003_Floor2`). Cards change color dynamically:
  * **Healthy (Green)**: Active, no current alerts.
  * **Warning (Yellow)**: Non-critical alerts active (e.g., retry spike).
  * **Critical (Red)**: Critical alerts active (e.g., microwave interference).
* **Refresh Data Button**: Manually forces Streamlit to fetch fresh data from FastAPI endpoints.
* **Trigger Simulation Minute Button**: Forces a manual background simulator step, injecting telemetry immediately (useful for live presentations).

### Tab 1: Live Telemetry & Trends
* **Select AP Dropdown**: Focuses charts and cards on a specific Access Point.
* **QoE & Active Events Scorecard**: Displays live metrics for:
  * *QoE Score*: 0-100 score.
  * *Category*: Excellent/Good/Fair/Poor.
  * *Interference*: Displays active events, like "Microwave" or "None".
  * *Recommendation*: Action recommendation like "CHANNEL_CHANGE" or "NONE".
* **PHY / MAC Layer Metrics**: Horizontal cards showing:
  * *Airtime Utilization* (%), *Retry Rate* (%), *Noise Floor* (dBm), and *Avg RSSI / SNR* (dBm/dB).
* **Metrics Over Time Charts**: Interactive line and bar charts showing the historical trend of signal metrics, retries, utilization, and client density.

### Tab 2: Alerts & Recommendations
* **Active Alerts Pane**: Lists the 5 most recent anomalies. Formatted with severity tags:
  * `🔴 [HIGH]` for noise floor jumps (microwave).
  * `🟡 [MEDIUM]` for retry spikes.
  * `🔵 [LOW]` for airtime congestion.
* **RRM Policy Recommendations Table**: Searchable table displaying historical RRM actions, showing action type, starting setting, recommended target, confidence score, and clear logic explanation.

---

## Simulator Guide

### Legacy Simulator
The legacy system generates metrics using statistical normal distributions centered around base values. Anomaly states (`INTERFERENCE`, `SURGE`, `CONGESTED`) apply offsets to noise, clients, and retry rates. If run on a Windows machine, the legacy simulator attempts to query host adapter interfaces using `netsh wlan show interfaces` to overwrite simulated AP_001 metrics with real local stats.

### Realistic Simulator
The realistic simulator uses networking models to calculate causal values:
* **Log-Distance Path Loss Model**: Calculates client RSSI based on distance:
  $$\text{RSSI}(d) = \text{RSSI}(d_0) - 10 \cdot \eta \cdot \log_{10}\left(\frac{d}{d_0}\right)$$
  Where $d_0 = 1.0\text{m}$, $\text{RSSI}(d_0) = -35\text{dBm}$, and Path Loss Exponent $\eta = 3.0$.
* **Channel Capacity & Airtime**: Maps channel width (20, 40, 80 MHz) to capacities (144, 300, 866 Mbps). Computes airtime occupancy based on client request demands versus capacity.
* **Collision-Based Retry Heuristics**: Calculates retry rate as a function of SNR and airtime utilization:
  $$\text{Retry Rate} = \text{Retry Base} \times \left(1 + \left(\frac{\text{Utilization}}{100}\right)^2\right)$$
* **QoE Calculation**: Scores network health out of 100, subtracting penalties for high retry rates (critical latency impact), low SNR ($<25$ dB), and high utilization ($>70\%$).

### Simulation Scenario Cycles (Interference Events)
The background simulator worker manages a loop. Every 25 ticks (minutes), it cycles through three preset interference event scenarios:
1. **Ticks 5-9**: `Microwave` (Noise Floor boosts by $+15\text{dB}$).
2. **Ticks 15-19**: `BLE Congestion` (Noise Floor $+3\text{dB}$, Airtime utilization $+5\%$).
3. **Ticks 20-24**: `Neighbor AP Congestion` (Airtime utilization $+20\%$).

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
  SIMULATOR_MODE=realistic
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
