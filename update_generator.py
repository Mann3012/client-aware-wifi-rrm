import os

with open('src/simulator/generator.py', 'r') as f:
    content = f.read()

# 1. Add mode and sim_tick
content = content.replace(
    'self.seed_hours = int(os.getenv("SEED_HOURS", 6))',
    'self.seed_hours = int(os.getenv("SEED_HOURS", 6))\n        self.simulator_mode = os.getenv("SIMULATOR_MODE", "realistic")\n        self.sim_tick = 0'
)

# 2. Increment tick in step
content = content.replace(
    '        try:\n            # Randomly trigger',
    '        try:\n            self.sim_tick += 1\n            # Randomly trigger'
)
content = content.replace(
    '        try:\n            # Check if telemetry',
    '        try:\n            self.sim_tick += 1\n            # Check if telemetry'
) # for seed data - wait, seed data loops using step

# 3. Modify execute_simulation_step
old_logic = '''        for ap_id, state in self.states.items():
            # 1. Advance simulation state
            if state["anomaly_ticks"] > 0:
                state["anomaly_ticks"] -= 1
                if state["anomaly_ticks"] == 0:
                    state["anomaly_state"] = "NORMAL"

            # Apply anomaly multipliers
            noise_mod = 0.0
            retry_mod = 0.0
            client_mod = 0
            airtime_mod = 0.0

            if state["anomaly_state"] == "INTERFERENCE":
                noise_mod = random.uniform(12.0, 22.0)
                retry_mod = random.uniform(0.15, 0.35)
                airtime_mod = random.uniform(0.05, 0.15)
            elif state["anomaly_state"] == "SURGE":
                client_mod = random.randint(15, 30)
                retry_mod = random.uniform(0.01, 0.05)
                airtime_mod = random.uniform(0.20, 0.40)
            elif state["anomaly_state"] == "CONGESTED":
                retry_mod = random.uniform(0.10, 0.22)
                airtime_mod = random.uniform(0.40, 0.65)

            # 2. Calculate values
            local_stats = {}
            if ap_id == "AP_001_Floor1":
                local_stats = self._get_local_wifi_stats()

            client_count = max(0, int(random.normalvariate(state["base_clients"] + client_mod, 2.0)))
            noise_floor = min(-70.0, max(-105.0, random.normalvariate(state["base_noise_floor"] + noise_mod, 1.5)))
            
            if local_stats and "rssi" in local_stats:
                rssi = local_stats["rssi"]
                if "channel" in local_stats:
                    state["channel"] = local_stats["channel"]
                logger.info(f"Using live host RSSI: {rssi} dBm, Channel: {state['channel']} for {ap_id}")
            else:
                rssi = random.normalvariate(-65.0, 4.0) if client_count > 0 else -95.0

            snr = max(0.0, rssi - noise_floor) if client_count > 0 else 0.0
            retry_rate = min(1.0, max(0.0, random.normalvariate(state["base_retry_rate"] + retry_mod, 0.01)))
            
            client_load = client_count * 0.02
            retry_load = retry_rate * 0.5
            airtime_util = min(0.98, max(0.02, random.normalvariate(state["base_airtime_util"] + client_load + retry_load + airtime_mod, 0.03)))

            # Create Telemetry Record
            telemetry_row = Telemetry(
                timestamp=timestamp,
                ap_id=ap_id,
                channel=state["channel"],
                rssi=round(rssi, 2),
                snr=round(snr, 2),
                noise_floor=round(noise_floor, 2),
                airtime_utilization=round(airtime_util, 4),
                retry_rate=round(retry_rate, 4),
                client_count=client_count
            )'''

new_logic = '''        cycle_tick = self.sim_tick % 25
        
        active_event = None
        if 5 <= cycle_tick < 10:
            from src.realistic_simulator.models import InterferenceEvent
            active_event = InterferenceEvent("Microwave", noise_boost_db=15.0, airtime_boost_percent=0.0, duration_minutes=5, active=True)
        elif 15 <= cycle_tick < 20:
            from src.realistic_simulator.models import InterferenceEvent
            active_event = InterferenceEvent("BLE Congestion", noise_boost_db=3.0, airtime_boost_percent=5.0, duration_minutes=5, active=True)
        elif 20 <= cycle_tick < 25:
            from src.realistic_simulator.models import InterferenceEvent
            active_event = InterferenceEvent("Neighbor AP Congestion", noise_boost_db=0.0, airtime_boost_percent=20.0, duration_minutes=5, active=True)

        for ap_id, state in self.states.items():
            if self.simulator_mode == "realistic":
                from src.realistic_simulator.models import APState, ClientState
                from src.realistic_simulator.telemetry_simulator import TelemetrySimulator
                ap_state = APState(ap_id=ap_id, channel=state["channel"], channel_width=40, base_noise=-95.0)
                sim = TelemetrySimulator(ap_state)
                clients = [
                    ClientState(client_id=f"{ap_id}_C1", distance_meters=5.0, demand_mbps=10.0),
                    ClientState(client_id=f"{ap_id}_C2", distance_meters=15.0, demand_mbps=20.0),
                    ClientState(client_id=f"{ap_id}_C3", distance_meters=20.0, demand_mbps=30.0),
                ]
                record = sim.generate_telemetry(clients, event=active_event)
                
                rssi = record.rssi
                noise_floor = record.noise_floor
                snr = record.snr
                airtime_util = record.airtime_utilization / 100.0
                retry_rate = record.retry_rate
                client_count = record.client_count
                qoe_score = record.qoe_score
                qoe_category = record.qoe_category
                interference_type = active_event.event_type if active_event else "None"
                
            else:
                if state["anomaly_ticks"] > 0:
                    state["anomaly_ticks"] -= 1
                    if state["anomaly_ticks"] == 0:
                        state["anomaly_state"] = "NORMAL"

                noise_mod = 0.0
                retry_mod = 0.0
                client_mod = 0
                airtime_mod = 0.0

                if state["anomaly_state"] == "INTERFERENCE":
                    noise_mod = random.uniform(12.0, 22.0)
                    retry_mod = random.uniform(0.15, 0.35)
                    airtime_mod = random.uniform(0.05, 0.15)
                elif state["anomaly_state"] == "SURGE":
                    client_mod = random.randint(15, 30)
                    retry_mod = random.uniform(0.01, 0.05)
                    airtime_mod = random.uniform(0.20, 0.40)
                elif state["anomaly_state"] == "CONGESTED":
                    retry_mod = random.uniform(0.10, 0.22)
                    airtime_mod = random.uniform(0.40, 0.65)

                local_stats = {}
                if ap_id == "AP_001_Floor1":
                    local_stats = self._get_local_wifi_stats()

                client_count = max(0, int(random.normalvariate(state["base_clients"] + client_mod, 2.0)))
                noise_floor = min(-70.0, max(-105.0, random.normalvariate(state["base_noise_floor"] + noise_mod, 1.5)))
                
                if local_stats and "rssi" in local_stats:
                    rssi = local_stats["rssi"]
                    if "channel" in local_stats:
                        state["channel"] = local_stats["channel"]
                else:
                    rssi = random.normalvariate(-65.0, 4.0) if client_count > 0 else -95.0

                snr = max(0.0, rssi - noise_floor) if client_count > 0 else 0.0
                retry_rate = min(1.0, max(0.0, random.normalvariate(state["base_retry_rate"] + retry_mod, 0.01)))
                
                client_load = client_count * 0.02
                retry_load = retry_rate * 0.5
                airtime_util = min(0.98, max(0.02, random.normalvariate(state["base_airtime_util"] + client_load + retry_load + airtime_mod, 0.03)))
                qoe_score = None
                qoe_category = None
                interference_type = "None"

            telemetry_row = Telemetry(
                timestamp=timestamp,
                ap_id=ap_id,
                channel=state["channel"],
                rssi=round(rssi, 2),
                snr=round(snr, 2),
                noise_floor=round(noise_floor, 2),
                airtime_utilization=round(airtime_util, 4),
                retry_rate=round(retry_rate, 4),
                client_count=client_count,
                qoe_score=qoe_score,
                qoe_category=qoe_category,
                interference_type=interference_type
            )'''

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    with open('src/simulator/generator.py', 'w') as f:
        f.write(content)
    print('SUCCESS')
else:
    print('FAILED TO MATCH')
