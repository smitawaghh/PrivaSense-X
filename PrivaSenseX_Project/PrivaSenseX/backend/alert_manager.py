"""Create role-specific dashboard alerts according to the demo policy."""

from backend.database import get_users, save_notification

def build_notifications(result: dict, sensor_data: dict, incident_id: int):
    severity = result["severity"]
    if severity == "NORMAL":
        return []

    users = get_users()
    generated = []

    for user in users:
        if not user["active"]:
            continue

        role = user["role"]
        authorized = True
        message = None

        if role == "Resident":
            message = (
                f"Safety alert: {result['event']}. "
                "Follow your personal safety plan and move away from the suspected hazard."
            )
        elif role == "Caregiver":
            message = (
                f"Assistance alert for your assigned resident: {result['event']}. "
                "Please check on the resident using your agreed care plan."
            )
        elif role == "Responder":
            authorized = (
                severity == "CRITICAL" and bool(user["responder_authorized"])
            )
            if authorized:
                message = (
                    f"Authorized critical incident: {result['event']}. "
                    f"Temperature: {sensor_data['temperature_c']} C; "
                    f"gas sensor raw value: {sensor_data['gas_raw']}."
                )
        elif role == "Admin":
            message = (
                f"System audit notification: {result['event']} "
                f"(severity: {severity})."
            )

        if authorized and message:
            recipient = {
                "username": user["username"],
                "role": role,
            }
            save_notification(incident_id, recipient, message)
            generated.append({**recipient, "message": message})

    return generated
