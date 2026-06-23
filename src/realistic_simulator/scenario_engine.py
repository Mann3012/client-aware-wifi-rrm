from dataclasses import dataclass
from typing import Optional, Tuple
from src.realistic_simulator.models import InterferenceEvent

@dataclass
class Scenario:
    name: str
    interference: Optional[InterferenceEvent]
    client_demand_multiplier: float = 1.0
    client_count_override: Optional[Tuple[int, int]] = None
    client_distance_override: Optional[float] = None
    
    # Metadata for visibility & dashboard
    interference_type: str = "None"
    expected_noise: float = -95.0
    expected_snr_range: Tuple[float, float] = (25.0, 45.0)
    expected_recommendation: str = "NONE"

class ScenarioEngine:
    """
    Manages explicit scenarios for repeatable simulation demonstrations.
    """
    
    SCENARIO_NAMES = [
        "Normal Office",
        "Bluetooth Storm",
        "Microwave Burst",
        "Neighbor AP Congestion",
        "Crowded Conference Room",
        "Weak Signal Corner"
    ]

    @staticmethod
    def get_scenario(name: str) -> Scenario:
        if name == "Normal Office":
            return Scenario(
                name="Normal Office",
                interference=None,
                client_demand_multiplier=1.0,
                client_count_override=(2, 8),
                interference_type="None",
                expected_noise=-95.0,
                expected_snr_range=(25.0, 45.0),
                expected_recommendation="NONE"
            )
        elif name == "Microwave Burst":
            return Scenario(
                name="Microwave Burst",
                interference=InterferenceEvent(
                    event_type="MICROWAVE",
                    noise_boost_db=15.0,
                    airtime_boost_percent=0.0,
                    duration_minutes=5,
                    active=True
                ),
                client_demand_multiplier=1.0,
                interference_type="MICROWAVE",
                expected_noise=-80.0,
                expected_snr_range=(5.0, 15.0),
                expected_recommendation="CHANNEL_CHANGE"
            )
        elif name == "Bluetooth Storm":
            return Scenario(
                name="Bluetooth Storm",
                interference=InterferenceEvent(
                    event_type="BLE",
                    noise_boost_db=5.0,
                    airtime_boost_percent=5.0,
                    duration_minutes=5,
                    active=True
                ),
                client_demand_multiplier=1.0,
                interference_type="BLE",
                expected_noise=-90.0,
                expected_snr_range=(15.0, 25.0),
                expected_recommendation="CHANNEL_CHANGE"
            )
        elif name == "Neighbor AP Congestion":
            return Scenario(
                name="Neighbor AP Congestion",
                interference=InterferenceEvent(
                    event_type="Neighbor AP",
                    noise_boost_db=10.0,
                    airtime_boost_percent=25.0,
                    duration_minutes=5,
                    active=True
                ),
                client_demand_multiplier=1.0,
                interference_type="Neighbor AP",
                expected_noise=-85.0,
                expected_snr_range=(10.0, 20.0),
                expected_recommendation="LOAD_BALANCE"
            )
        elif name == "Crowded Conference Room":
            return Scenario(
                name="Crowded Conference Room",
                interference=None,
                client_demand_multiplier=3.0,
                client_count_override=(25, 50),
                interference_type="None",
                expected_noise=-95.0,
                expected_snr_range=(20.0, 40.0),
                expected_recommendation="WIDTH_ADJUST"
            )
        elif name == "Weak Signal Corner":
            return Scenario(
                name="Weak Signal Corner",
                interference=None,
                client_demand_multiplier=1.0,
                client_distance_override=30.0, # Push distance far away
                interference_type="None",
                expected_noise=-95.0,
                expected_snr_range=(5.0, 15.0),
                expected_recommendation="POWER_INCREASE"
            )
        
        # Default fallback
        return ScenarioEngine.get_scenario("Normal Office")
