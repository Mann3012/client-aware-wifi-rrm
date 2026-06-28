"""
Digital Twin State Manager for the Client-Aware WiFi RRM Simulator.

Maintains the single source of truth for the physical and MAC state of the network.
Used by the TelemetrySimulator to generate metrics.
"""

from typing import Dict
import logging

from src.realistic_simulator.models import DigitalTwinState, APDigitalTwin, ClientDigitalTwin, ChannelStateTwin, APState, ClientState

logger = logging.getLogger("RRM.DigitalTwin")

class DigitalTwinManager:
    """Manages the lifecycle of the Digital Twin state."""
    
    def __init__(self):
        self.state = DigitalTwinState()
        
    def sync_ap(self, ap_state: APState) -> APDigitalTwin:
        """Syncs an AP from legacy APState to Digital Twin."""
        ap_dt = APDigitalTwin(
            ap_id=ap_state.ap_id,
            channel=ap_state.channel,
            channel_width_mhz=ap_state.channel_width,
            tx_power_dbm=ap_state.tx_power_dbm,
            antenna_gain_dbi=ap_state.antenna_gain_dbi,
            noise_figure_db=ap_state.noise_figure_db,
            bss_color=ap_state.bss_color,
            x=ap_state.x,
            y=ap_state.y
        )
        self.state.aps[ap_state.ap_id] = ap_dt
        return ap_dt
        
    def sync_clients(self, ap_id: str, clients: list[ClientState]) -> list[ClientDigitalTwin]:
        """Syncs clients from legacy ClientState to Digital Twin."""
        dt_clients = []
        for c in clients:
            c_dt = ClientDigitalTwin(
                client_id=c.client_id,
                ap_id=ap_id,
                x=c.x,
                y=c.y,
                velocity_mps=c.velocity_mps,
                direction_rad=c.direction_rad,
                device_type=c.device_type,
                application_type=c.application_type,
                demand_mbps=c.demand_mbps,
                antenna_gain_dbi=c.antenna_gain_dbi,
                noise_figure_db=c.noise_figure_db,
                mobility_model=c.mobility_model
            )
            self.state.clients[c.client_id] = c_dt
            dt_clients.append(c_dt)
        return dt_clients
        
    def get_state(self) -> DigitalTwinState:
        return self.state
