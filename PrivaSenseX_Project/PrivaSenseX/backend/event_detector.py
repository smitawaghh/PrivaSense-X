"""Classify the simulated sensor values into event severity."""

from backend.config import TEMP_WARNING_C, TEMP_CRITICAL_C, GAS_CRITICAL_RAW

def detect_event(sensor_data: dict) -> dict:
    temp = float(sensor_data["temperature_c"])
    gas = int(sensor_data["gas_raw"])
    motion = bool(sensor_data["motion"])

    reasons = []
    if temp >= TEMP_CRITICAL_C:
        reasons.append("Critical temperature threshold reached")
    elif temp >= TEMP_WARNING_C:
        reasons.append("Temperature warning threshold reached")

    if gas >= GAS_CRITICAL_RAW:
        reasons.append("Gas sensor threshold exceeded")

    if temp >= TEMP_CRITICAL_C or gas >= GAS_CRITICAL_RAW:
        severity = "CRITICAL"
    elif temp >= TEMP_WARNING_C:
        severity = "WARNING"
    else:
        severity = "NORMAL"

    if severity == "NORMAL":
        event_name = "Normal environmental conditions"
    elif temp >= TEMP_CRITICAL_C and gas >= GAS_CRITICAL_RAW:
        event_name = "Combined temperature and gas alert"
    elif temp >= TEMP_CRITICAL_C:
        event_name = "Critical temperature alert"
    elif gas >= GAS_CRITICAL_RAW:
        event_name = "Gas alert"
    else:
        event_name = "High temperature warning"

    return {
        "event": event_name,
        "severity": severity,
        "reasons": reasons,
        "motion": motion,
    }
