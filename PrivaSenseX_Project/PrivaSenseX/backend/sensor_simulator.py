"""Software simulator for the TMP36-style temperature, gas and PIR inputs."""

SCENARIOS = {
    "Normal conditions": {
        "temperature_c": 30.0, "gas_raw": 100, "motion": False
    },
    "Temperature warning": {
        "temperature_c": 50.0, "gas_raw": 100, "motion": False
    },
    "Critical temperature": {
        "temperature_c": 65.0, "gas_raw": 100, "motion": True
    },
    "Gas alert": {
        "temperature_c": 30.0, "gas_raw": 600, "motion": False
    },
    "Combined critical alert": {
        "temperature_c": 65.0, "gas_raw": 600, "motion": True
    },
    "Motion only": {
        "temperature_c": 30.0, "gas_raw": 100, "motion": True
    },
}

def get_sensor_data(scenario_name: str) -> dict:
    """Return a copy of one simulated sensor scenario."""
    if scenario_name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_name}")
    return dict(SCENARIOS[scenario_name])
