import os
import requests
import json
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
    page_title="WiFi Radio Resource Management (RRM) Digital Twin",
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
    .explain-panel { background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 0.5rem; padding: 1rem; }
</style>
""", unsafe_allow_html=True)

# Helper function to query the API
def fetch_from_api(endpoint: str, params: dict = None) -> list:
    try:
        response = requests.get(f"{API_URL}{endpoint}", params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except requests.exceptions.ConnectionError:
        return []

def set_scenario(ap_id: str, scenario_name: str):
    try:
        requests.post(f"{API_URL}/scenario/set", params={"ap_id": ap_id, "scenario_name": scenario_name}, timeout=5)
    except:
        pass

def trigger_simulator_step() -> bool:
    try:
        res = requests.post(f"{API_URL}/simulator/trigger", timeout=5)
        return res.status_code == 200
    except Exception:
        return False

# Header layout
st.markdown('<div class="main-header">Client-Aware WiFi Digital Twin</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Live Physical Network Simulation & Explainable RRM Decisions</div>', unsafe_allow_html=True)

# Sidebar controls
st.sidebar.image("https://img.icons8.com/color/96/wifi.png", width=64)
st.sidebar.markdown("### Controls & Actions")

if st.sidebar.button("🔄 Refresh Data", width='stretch'):
    st.rerun()

if st.sidebar.button("⚡ Trigger Simulation Step", width='stretch'):
    if trigger_simulator_step():
        st.sidebar.success("Step generated!")
        st.rerun()
    else:
        st.sidebar.error("Failed to step simulator.")

st.sidebar.markdown("---")
st.sidebar.markdown("### Manual Scenario Control")

ap_summaries = fetch_from_api("/ap-status")
if ap_summaries:
    ap_ids = [ap["ap_id"] for ap in ap_summaries]
    selected_ap = st.selectbox("Select AP:", ap_ids)
    
    SCENARIOS = [
        "Normal Office",
        "Bluetooth Storm",
        "Microwave Burst",
        "Neighbor AP Congestion",
        "Crowded Conference Room",
        "Weak Signal Corner"
    ]
    force_scen = st.sidebar.selectbox("Force Scenario:", SCENARIOS)
    if st.sidebar.button("Apply Scenario"):
        set_scenario(selected_ap, force_scen)
        st.sidebar.success(f"Forced {force_scen}")
        st.rerun()

# 1. Render AP Health Cards Row
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
                    <span class="metric-label">Connected Clients:</span> <b>{ap['client_count']}</b><br/>
                    <span class="metric-label">Active Alerts:</span> <b>{ap['active_alert_count']}</b><br/>
                    <span class="metric-label">Latest Action:</span> <code style="font-size:0.75rem;">{ap['recent_recommendation']}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.warning("No Access Point summary data available. Start the backend first.")


if ap_summaries and selected_ap:
    
    # 2. Scenario Timeline
    st.markdown("### Scenario Event Timeline")
    history = fetch_from_api("/scenario/history", params={"ap_id": selected_ap, "limit": 5})
    if history:
        timeline_strs = []
        for h in reversed(history):
            t_str = pd.to_datetime(h['start_time']).strftime('%H:%M')
            evt_str = f"**{t_str} {h['scenario_name']}**"
            if h.get('recommendation_triggered'):
                evt_str += f" → `{h['recommendation_triggered']}`"
            timeline_strs.append(evt_str)
        
        st.markdown(" | ".join(timeline_strs))
    
    tab1, tab2, tab3 = st.tabs(["🎯 Root Cause & Topology", "📊 Physics Telemetry", "🔔 Recommendations & Alerts"])
    
    # Fetch data once
    telemetry_data = fetch_from_api("/telemetry", params={"ap_id": selected_ap, "limit": 100})
    if telemetry_data:
        df = pd.DataFrame(telemetry_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        latest_row = df.iloc[-1]
        
        recs = fetch_from_api("/recommendations", params={"limit": 5, "ap_id": selected_ap})
        alerts = fetch_from_api("/alerts", params={"limit": 50, "ap_id": selected_ap})
        
        # TAB 1: ROOT CAUSE & TOPOLOGY
        with tab1:
            rc_col1, rc_col2 = st.columns([1, 1])
            
            with rc_col1:
                st.markdown("#### Explainability Panel")
                st.markdown('<div class="explain-panel">', unsafe_allow_html=True)
                
                if recs:
                    top_rec = recs[0]
                    expected_gain = top_rec.get("expected_qoe_gain", 0.0)
                    
                    st.markdown(f"**Current Scenario:** {latest_row.get('scenario_name', 'Unknown')}")
                    st.markdown(f"**Root Cause:** `{top_rec.get('root_cause', 'NONE')}`")
                    st.markdown("---")
                    
                    st.markdown("**Causal Metric Chain:**")
                    # Format multiline reason
                    lines = top_rec['reason'].split('\n')
                    for line in lines:
                        if ':' in line:
                            st.markdown(f"- {line}")
                            
                    st.markdown("---")
                    st.markdown(f"**Action Recommendation:** `{top_rec['action']}` (Confidence: {top_rec['confidence']*100:.1f}%)")
                    st.markdown(f"**Expected QoE After Action:** {min(100.0, latest_row.get('qoe_score', 0.0) + expected_gain):.1f} (+{expected_gain:.1f})")
                else:
                    st.info("No recommendations generated yet.")
                    
                st.markdown('</div>', unsafe_allow_html=True)
                
            with rc_col2:
                st.markdown("#### Live Client Topology")
                if history and history[0].get("client_topology_snapshot"):
                    try:
                        topology = json.loads(history[0]["client_topology_snapshot"])
                        if topology:
                            df_top = pd.DataFrame(topology)
                            
                            import plotly.express as px
                            fig = px.scatter(df_top, x="x", y="y", text="id", title="Floor Plan", range_x=[0, 50], range_y=[0, 50])
                            
                            # Add AP at center (usually 25, 25 based on random.uniform(0, 50) but we don't have exact AP coords in snapshot)
                            # Assuming AP is near the center of clients.
                            fig.add_scatter(x=[df_top['x'].mean()], y=[df_top['y'].mean()], mode='markers+text', text=["AP"], marker=dict(size=15, color="red"))
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No clients in topology.")
                    except:
                        st.info("Error rendering topology.")
                else:
                    st.info("Topology snapshot not available.")

        # TAB 2: PHYSICS TELEMETRY
        with tab2:
            st.markdown("#### Physical Environment Summary")
            p_col1, p_col2, p_col3, p_col4, p_col5 = st.columns(5)
            p_col1.metric("Distance (Avg / Max)", f"{latest_row.get('distance', 0)}m / {latest_row.get('max_distance', 0)}m")
            p_col2.metric("Wall Count (Loss)", f"{latest_row.get('wall_count', 0)} ({latest_row.get('wall_loss', 0)} dB)")
            p_col3.metric("Frequency", f"{latest_row.get('freq_mhz', 0)} MHz")
            p_col4.metric("Tx Power", f"{latest_row.get('tx_power', 0)} dBm")
            p_col5.metric("Interference Event", f"{latest_row.get('interference_type', 'None')}")
            
            st.markdown("---")
            
            st.markdown("#### Causal Chain Over Time")
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.markdown("**1. Client Distance (m)**")
                if 'distance' in df.columns:
                    st.line_chart(df['distance'])
                
                st.markdown("**2. Signal Quality (RSSI, SNR & Noise)**")
                signal_df = df[['rssi', 'snr', 'noise_floor']]
                st.line_chart(signal_df)
                
                st.markdown("**3. Packet Retry Rate**")
                st.line_chart(df['retry_rate'])
                
            with chart_col2:
                st.markdown("**4. QoE Score**")
                if 'qoe_score' in df.columns:
                    st.line_chart(df['qoe_score'])
                
                st.markdown("**Airtime Spectrum Occupancy**")
                st.line_chart(df['airtime_utilization'])
                
                st.markdown("**Connected Client Density**")
                st.bar_chart(df['client_count'])

        # TAB 3: RECOMMENDATIONS & ALERTS
        with tab3:
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("#### Ranked RRM Recommendations")
                if recs:
                    df_recs = pd.DataFrame(recs)
                    df_recs['timestamp'] = pd.to_datetime(df_recs['timestamp'])
                    if 'expected_qoe_gain' in df_recs.columns:
                        display_recs = df_recs[['timestamp', 'action', 'confidence', 'expected_qoe_gain', 'root_cause']]
                    else:
                        display_recs = df_recs[['timestamp', 'action', 'confidence', 'root_cause']]
                    st.dataframe(display_recs, width='stretch', hide_index=True)
                else:
                    st.info("No recommendations.")
                    
            with col_b:
                st.markdown("#### Scenario-Aware Alerts")
                if alerts:
                    df_alerts = pd.DataFrame(alerts)
                    df_alerts['timestamp'] = pd.to_datetime(df_alerts['timestamp'])
                    
                    for _, alert in df_alerts.head(5).iterrows():
                        severity = "🔴" if "interference" in alert['alert_type'] else "🟡"
                        st.markdown(f"**{severity} {alert['alert_type'].replace('_', ' ').title()}**")
                        st.caption(f"{alert['description']}")
                        st.markdown("---")
                else:
                    st.success("No active anomalies.")
