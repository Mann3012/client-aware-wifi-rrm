import os
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load configurations
load_dotenv()
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = os.getenv("API_PORT", "8000")
API_URL = f"http://{API_HOST}:{API_PORT}"

# Configure Streamlit page options
st.set_page_config(
    page_title="WiFi Radio Resource Management (RRM) Dashboard",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium CSS styles
st.markdown("""
<style>
    .main-header {
        font-family: 'Outfit', 'Inter', sans-serif;
        color: #0F172A;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-family: 'Inter', sans-serif;
        color: #64748B;
        font-size: 1.05rem;
        margin-bottom: 1.8rem;
    }
    .health-card {
        padding: 1.25rem;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    .status-healthy { background-color: #ECFDF5; border-left: 5px solid #10B981; }
    .status-warning { background-color: #FFFBEB; border-left: 5px solid #F59E0B; }
    .status-critical { background-color: #FEF2F2; border-left: 5px solid #EF4444; }
    .status-title { font-weight: bold; font-size: 1.1rem; color: #1E293B; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #0F172A; }
    .metric-label { font-size: 0.85rem; color: #64748B; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# Helper function to query the API
def fetch_from_api(endpoint: str, params: dict = None) -> list:
    try:
        response = requests.get(f"{API_URL}{endpoint}", params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error ({response.status_code}): {response.text}")
            return []
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to FastAPI server at {API_URL}. Make sure it is running.")
        return []

# Helper function to trigger a simulator step
def trigger_simulator_step() -> bool:
    try:
        res = requests.post(f"{API_URL}/simulator/trigger", timeout=5)
        return res.status_code == 200
    except Exception:
        return False

# Header layout
st.markdown('<div class="main-header">Client-Aware WiFi RRM Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Live Telemetry Analysis, EWMA/CUSUM Anomaly Detection & Automatic Optimization Recommendations</div>', unsafe_allow_html=True)

# Sidebar controls
st.sidebar.image("https://img.icons8.com/color/96/wifi.png", width=64)
st.sidebar.markdown("### Controls & Actions")

if st.sidebar.button("🔄 Refresh Data", width='stretch'):
    st.rerun()

if st.sidebar.button("⚡ Trigger Simulation Minute", width='stretch'):
    if trigger_simulator_step():
        st.sidebar.success("Generated next telemetry step!")
        st.rerun()
    else:
        st.sidebar.error("Failed to step simulator.")

st.sidebar.markdown("---")
st.sidebar.markdown("### Simulation Config")
st.sidebar.info(
    "The Telemetry Simulator runs in the background of the FastAPI application. "
    "To view anomalies, use the button above to simulate steps instantly or wait for the automatic update loop."
)

# 1. Fetch AP Summaries
ap_summaries = fetch_from_api("/ap-status")

# 2. Render AP Health Cards Row
if ap_summaries:
    st.markdown("### Access Point Status Scorecard")
    cols = st.columns(len(ap_summaries))
    
    for idx, ap in enumerate(ap_summaries):
        with cols[idx]:
            status_class = "status-healthy"
            status_icon = "🟢"
            if ap["status"] == "Warning":
                status_class = "status-warning"
                status_icon = "🟡"
            elif ap["status"] == "Critical":
                status_class = "status-critical"
                status_icon = "🔴"
                
            st.markdown(f"""
            <div class="health-card {status_class}">
                <div class="status-title">{status_icon} {ap['ap_id']}</div>
                <div style="margin-top: 0.5rem;">
                    <span class="metric-label">Status:</span> <b>{ap['status']}</b><br/>
                    <span class="metric-label">Active Channel:</span> <b>Ch {ap['channel']}</b><br/>
                    <span class="metric-label">Connected Clients:</span> <b>{ap['client_count']}</b><br/>
                    <span class="metric-label">Active Alerts (30m):</span> <b>{ap['active_alert_count']}</b><br/>
                    <span class="metric-label">Latest Action:</span> <code style="font-size:0.75rem;">{ap['recent_recommendation']}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.warning("No Access Point summary data available. Start the backend first.")

# 3. Main Dashboard Layout: Left = Charts, Right = Alerts/Recommendations
tab1, tab2 = st.tabs(["📊 Live Telemetry & Trends", "🔔 Alerts & Recommendations"])

with tab1:
    if ap_summaries:
        ap_ids = [ap["ap_id"] for ap in ap_summaries]
        selected_ap = st.selectbox("Select Access Point to Analyze Details:", ap_ids)
        
        # Fetch detailed historical telemetry for the selected AP (last 100 points)
        telemetry_data = fetch_from_api("/telemetry", params={"ap_id": selected_ap, "limit": 100})
        
        if telemetry_data:
            df = pd.DataFrame(telemetry_data)
            # Parse timestamps
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            latest_row = df.iloc[-1]
            
            # --- New QoE & Interference Row ---
            st.markdown("#### Quality of Experience & Active Events")
            q_col1, q_col2, q_col3, q_col4 = st.columns(4)
            qoe_score = latest_row.get("qoe_score", "N/A")
            qoe_cat = latest_row.get("qoe_category", "N/A")
            interference = latest_row.get("interference_type", "None")
            
            # Try to get the latest recommendation for this AP
            recs = fetch_from_api("/recommendations", params={"limit": 1})
            latest_rec = "NONE"
            if recs and len(recs) > 0 and recs[0]["ap_id"] == selected_ap:
                latest_rec = recs[0]["action"]
                
            q_col1.metric("QoE Score", f"{qoe_score}")
            q_col2.metric("Category", f"{qoe_cat}")
            q_col3.metric("Interference", f"{interference}")
            q_col4.metric("Recommendation", f"{latest_rec}")
            
            st.markdown("---")
            
            # Sub-metrics Row
            st.markdown("#### PHY / MAC Layer Metrics")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Airtime Utilization", f"{int(latest_row['airtime_utilization']*100)}%", delta=None)
            m_col2.metric("Retry Rate", f"{latest_row['retry_rate']:.2%}", delta=None)
            m_col3.metric("Noise Floor", f"{latest_row['noise_floor']} dBm", delta=None)
            m_col4.metric("Avg RSSI / SNR", f"{latest_row['rssi']} dBm / {latest_row['snr']} dB", delta=None)
            
            # Plot trends
            st.markdown("#### Metrics Over Time")
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                # Signal strength vs Noise Floor
                st.markdown("**Signal Quality (RSSI, SNR & Noise Floor)**")
                signal_df = df[['rssi', 'snr', 'noise_floor']]
                st.line_chart(signal_df)
                
                # Retry rate
                st.markdown("**Packet Retry Rate**")
                st.line_chart(df['retry_rate'])
                
            with chart_col2:
                # Airtime utilization
                st.markdown("**Airtime Spectrum Occupancy**")
                st.line_chart(df['airtime_utilization'])
                
                # Client Count
                st.markdown("**Connected Client Density**")
                st.bar_chart(df['client_count'])
        else:
            st.info("No telemetry history available for this Access Point.")
    else:
        st.info("Start simulation to display telemetry trends.")

with tab2:
    # Fetch alerts and recommendations
    alerts = fetch_from_api("/alerts", params={"limit": 50})
    recommendations = fetch_from_api("/recommendations", params={"limit": 50})
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("#### Active Alerts")
        if alerts:
            df_alerts = pd.DataFrame(alerts)
            df_alerts['timestamp'] = pd.to_datetime(df_alerts['timestamp'])
            
            for _, alert in df_alerts.head(5).iterrows():
                if alert['alert_type'] == 'abnormal_interference':
                    severity = "🔴 [HIGH]"
                elif alert['alert_type'] == 'retry_spike':
                    severity = "🟡 [MEDIUM]"
                else:
                    severity = "🔵 [LOW]"
                    
                st.markdown(f"**{severity} {alert['alert_type'].replace('_', ' ').title()}**")
                st.caption(f"AP: {alert['ap_id']} | {alert['description']}")
                st.markdown("---")
        else:
            st.success("No anomalies detected in the system recently.")
            
    with col_b:
        st.markdown("#### RRM Policy Recommendations")
        if recommendations:
            df_recs = pd.DataFrame(recommendations)
            df_recs['timestamp'] = pd.to_datetime(df_recs['timestamp'])
            display_recs = df_recs[['timestamp', 'ap_id', 'action', 'current_value', 'recommended_value', 'confidence', 'reason']]
            st.dataframe(display_recs, width='stretch', hide_index=True)
        else:
            st.info("No RRM recommendations generated yet. Systems are operating optimally.")
