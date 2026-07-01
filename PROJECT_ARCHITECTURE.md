# Artista: WiFi RRM Project Architecture

This document details the software architecture, modular relationships, database flows, and lifecycle systems of the AI-Assisted Client-Aware WiFi Radio Resource Management (RRM) prototype.

---

## System Overview

The system is designed as a decoupled, closed-loop feedback architecture. It consists of an analytical backend that generates network metrics, evaluates performance, detects anomalies, and triggers adjustments, and a frontend dashboard that serves as a visualization layer.

```
       +---------------------------------------------+
       |             Streamlit Dashboard             |
       |                (Port 8501)                  |
       +----------------------+----------------------+
                              | REST API Calls
                              v
       +---------------------------------------------+
       |               FastAPI Backend               |
       |                (Port 8000)                  |
       +----------------------+----------------------+
                              | Database Sessions
                              v
+-----------------------------+-----------------------------+
|                      SQLite Database                      |
|                     (rrm_database.db)                     |
+-------+---------------------+---------------------+-------+
        ^                     ^                     |
        | Seeding/Saves       | Query History       | Telemetry &
        |                     |                     | Active Alerts
+-------+---------------------+---------------------+-------+
|                 Background Simulator Thread               |
|                 (Generator, Physics engine)               |
+-----------------------------+-----------------------------+
                              | Evaluates
                              v
       +---------------------------------------------+
       |              Analytics Engines              |
       |         (Change Detection & Policy)         |
       +---------------------------------------------+
```

---

## Data Flow Diagram

The diagram below represents the causal network physics and evaluation pipeline used in the **Realistic Simulator** mode to compute telemetry and recommend actions:

```
+-------------------------------------------------------+
|                     INPUT STATE                       |
|   - Client States (Distance, Throughput Demand)      |
|   - AP State (Channel, Width, Base Noise Floor)       |
|   - Interference Event (Microwave, BLE Congestion)    |
+--------------------------+----------------------------+
                           |
                           | (Calculates Path Loss)
                           v
              +--------------------------+
              |           RSSI           |
              +------------+-------------+
                           |
                           | (Calculates Environmental Interference)
                           v
              +--------------------------+
              |       Noise Floor        |
              +------------+-------------+
                           |
                           | (Calculates Signal Quality: RSSI - Noise)
                           v
              +--------------------------+
              |           SNR            |
              +------------+-------------+
                           |
                           | (Calculates Collisions & Retry Rate)
                           v
              +--------------------------+
              |        Retry Rate        |
              +------------+-------------+
                           |
                           | (Applies Metric Penalties)
                           v
               +--------------------------+
               |        QoE Score         |
               +------------+-------------+
                            |
                            | (Feature Extraction)
                            v
   +--------------------------------------------------+
   |               Diagnostic Engine                  |
   | Evaluates raw telemetry against thresholds to    |
   | generate ranked diagnoses with confidence levels.|
   +------------------------+-------------------------+
                            |
                            | (Yields Ranked Diagnoses)
                            v
   +--------------------------------------------------+
   |              Recommendation Engine               |
   | Formats diagnoses and associates mitigation      |
   | actions with expected QoE and retry improvements.|
   +------------------------+-------------------------+
                            |
                            | (Saved to DB / Rest APIs)
                            v
               +--------------------------+
               |   Streamlit Dashboard    |
               +--------------------------+
```

---

## System Component Details

The project is structured into six major components:

### 1. FastAPI (REST API Gateway)
* **Path**: [src/api/main.py](file:///c:/Users/l/Desktop/Artista/src/api/main.py), [src/api/routes.py](file:///c:/Users/l/Desktop/Artista/src/api/routes.py)
* **Function**: Serves as the integration hub. It coordinates the lifecycle of the background worker thread, handles HTTP endpoints, converts database ORM objects into Pydantic JSON responses, and exposes a manual controller endpoint to step the simulation.
* **Key Endpoints**:
  * `/ap-status`: Fetches calculated scorecards and active alert counts.
  * `/telemetry`: Retrieves time-series records for specific Access Points.
  * `/alerts`: Returns detected anomalies.
  * `/recommendations`: Exposes suggested optimization adjustments.
  * `/simulator/trigger`: Manually steps the background simulator.

### 2. SQLite Database (Persistence)
* **Path**: [src/database/connection.py](file:///c:/Users/l/Desktop/Artista/src/database/connection.py), [src/database/models.py](file:///c:/Users/l/Desktop/Artista/src/database/models.py)
* **Function**: An embedded database configured with `check_same_thread=False` to support concurrent write requests from background simulator threads and read operations from FastAPI. Schema mapping is done through SQLAlchemy.

### 3. Streamlit Dashboard (Visualization Interface)
* **Path**: [dashboard/app.py](file:///c:/Users/l/Desktop/Artista/dashboard/app.py)
* **Function**: A frontend server that visualizes data. It queries the backend API endpoints to render real-time charts (RSSI, Noise Floor, SNR, Retry Rate, Airtime, and Client Counts) and display categorized alerts.

### 4. Background Simulator Orchestrator
* **Path**: [src/simulator/generator.py](file:///c:/Users/l/Desktop/Artista/src/simulator/generator.py)
* **Function**: Runs a daemon thread that steps every $N$ seconds. In realistic mode, it simulates AP and client configurations; in legacy mode, it uses statistical distributions and can scrape Windows system wireless metrics using `netsh wlan show interfaces`.

### 5. Diagnostic Engine & Analytics
* **Path**: [src/realistic_simulator/recommendation_engine.py](file:///c:/Users/l/Desktop/Artista/src/realistic_simulator/recommendation_engine.py), [src/realistic_simulator/executive_summary.py](file:///c:/Users/l/Desktop/Artista/src/realistic_simulator/executive_summary.py), [src/analytics/policy_engine.py](file:///c:/Users/l/Desktop/Artista/src/analytics/policy_engine.py)
* **Function**: Decouples network evaluation from simulation state:
  * **Diagnostic Engine**: Evaluates raw telemetry metrics directly (e.g., path loss, airtime, retry rates) independent of the underlying scenario. It infers root causes and computes dynamic expected impacts (expected QoE gain and retry reduction).
  * **Executive Summary Generator**: Dynamically generates causal string reports based on telemetry combinations and diagnoses.
  * **Rule-Based Policy Engine**: Evaluates active statistical alerts to recommend actions, feeding channel adjustments back into simulator state.

### 6. Analytics Engine
* **Path**: [src/analytics/change_detection.py](file:///c:/Users/l/Desktop/Artista/src/analytics/change_detection.py)
* **Function**: Analyzes historical metrics to detect shifts and spikes. Uses EWMA for retry rates and airtime utilization, and CUSUM for noise floors.

---

## Major Module Interactions

The closed-loop interaction flow is structured as follows:

```
[Background Simulator]
        |
        | 1. Generates metrics
        v
[Database Telemetry Row]
        |
        | 2. Queries historical metrics slice (~40 points)
        v
[Change Detection Engine]
        |
        | 3. Computes EWMA & CUSUM, returns alerts
        v
[Database Alert Logs] <-------------+
        |                            |
        | 4. Reads telemetry & alerts| 5. Triggers Channel Change
        v                            |
[RRM Policy Engine] -----------------+
        |
        | 6. Generates recommendations
        v
[Database Recommendation Logs]
```

---

## Telemetry Lifecycle

Every simulation cycle executes the following data generation and validation lifecycle:

```
+-----------------------------------------------------------------------------+
| 1. Cycle Tick Evaluation                                                    |
|    - Increment cycle counter.                                               |
|    - Inject active events based on tick value (Microwave, BLE, etc.).       |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
| 2. Math & Physics Calculation                                               |
|    - Log-Distance Path Loss: RSSI = -35.0 - 30 * log10(Distance)            |
|    - Signal Quality: SNR = RSSI - Noise Floor (with event boosts)           |
|    - Spectral Efficiency: Airtime = (Traffic / Width Capacity) * 100        |
|    - Retry Rate = Retry Base (from SNR) * (1 + Airtime^2)                   |
|    - QoE Score = 100 - Penalties(Retry Rate, SNR, Utilization)              |
+-----------------------------------------------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------+
| 3. Persistence                                                              |
|    - Assemble Telemetry ORM object and commit transaction.                  |
+-----------------------------------------------------------------------------+
```

---

## Recommendation Lifecycle

The diagram below details how the recommendation engine generates and executes RRM optimizations:

```
                  +-----------------------------------+
                  |      New Telemetry Inserted       |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  | Fetch Active Alerts (Last 30 Min) |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |    Evaluate RRM Policy Rules      |
                  +-----------------+-----------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v (Rule Matched)                                v (No Match)
+-----------------------+                         +---------------------+
| Generate Rec Record   |                         |     Do Nothing      |
| - Action Type         |                         +---------------------+
| - Current Value       |
| - Recommended Target  |
| - Confidence Score    |
| - Reasoning Text      |
+-----------+-----------+
            |
            v
+-----------------------+
| Apply Channel Change  |
| (Updates Simulator    |
| State variables)      |
+-----------------------+
```

### Policy Rules Execution Details
1. **CHANNEL_CHANGE**: Triggered by high noise floor alerts ($>-85\text{dBm}$) or combined retry/congestion spikes. Selecting an alternative channel updates the simulator state variables immediately.
2. **WIDTH_ADJUST**: Triggered by high utilization and retries (narrows to $20\text{MHz}$) or low utilization and light client loads (expands to $80\text{MHz}$).
3. **POWER_ADJUST**: Triggered by low client RSSI/SNR (increases Tx power to $20\text{dBm}$) or high density with strong signals (decreases Tx power to $12\text{dBm}$).
