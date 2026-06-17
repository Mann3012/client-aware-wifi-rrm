with open("dashboard/app.py", "r", encoding="utf-8") as f:
    content = f.read()

old_metrics = """            # Sub-metrics Row
            latest_row = df.iloc[-1]
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Airtime Utilization", f"{int(latest_row['airtime_utilization']*100)}%", delta=None)
            m_col2.metric("Retry Rate", f"{latest_row['retry_rate']:.2%}", delta=None)
            m_col3.metric("Noise Floor", f"{latest_row['noise_floor']} dBm", delta=None)
            m_col4.metric("Avg RSSI / SNR", f"{latest_row['rssi']} dBm / {latest_row['snr']} dB", delta=None)"""

new_metrics = """            latest_row = df.iloc[-1]
            
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
            m_col4.metric("Avg RSSI / SNR", f"{latest_row['rssi']} dBm / {latest_row['snr']} dB", delta=None)"""

old_alerts = """    with col_a:
        st.markdown("#### Recent Anomalies & Alerts")
        if alerts:
            df_alerts = pd.DataFrame(alerts)
            df_alerts['timestamp'] = pd.to_datetime(df_alerts['timestamp'])
            # Select columns to display
            display_alerts = df_alerts[['timestamp', 'ap_id', 'alert_type', 'metric', 'value', 'threshold', 'description']]
            st.dataframe(display_alerts, use_container_width=True, hide_index=True)
        else:
            st.success("No anomalies detected in the system recently.")"""

new_alerts = """    with col_a:
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
            st.success("No anomalies detected in the system recently.")"""

content = content.replace(old_metrics, new_metrics)
content = content.replace(old_alerts, new_alerts)

with open("dashboard/app.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Dashboard updated successfully!")
