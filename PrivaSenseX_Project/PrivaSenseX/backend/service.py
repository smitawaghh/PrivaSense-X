"""Application service joining simulation, detection, storage and alerts."""

from backend.sensor_simulator import get_sensor_data
from backend.event_detector import detect_event
from backend.database import (
    initialize_database, save_sensor_reading, save_incident
)
from backend.alert_manager import build_notifications

def process_scenario(scenario_name: str, responder_authorized: bool | None = None):
    initialize_database()
    sensor_data = get_sensor_data(scenario_name)
    result = detect_event(sensor_data)

    save_sensor_reading(sensor_data, result["severity"], result["event"])

    incident_id = None
    notifications = []
    if result["severity"] != "NORMAL":
        incident_id = save_incident(sensor_data, result)
        notifications = build_notifications(result, sensor_data, incident_id)

    return {
        "sensor_data": sensor_data,
        "result": result,
        "incident_id": incident_id,
        "notifications": notifications,
    }
