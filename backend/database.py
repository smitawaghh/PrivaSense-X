"""SQLite persistence for users, current readings, incidents and alerts."""

import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timezone

from backend.config import DB_PATH

def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex(), digest.hex()

def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    _, candidate = hash_password(password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(candidate, hash_hex)

def initialize_database():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Resident','Caregiver','Responder','Admin')),
            salt_hex TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            responder_authorized INTEGER NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS current_state (
            id INTEGER PRIMARY KEY CHECK(id = 1),
            timestamp TEXT NOT NULL,
            temperature_c REAL NOT NULL,
            gas_raw INTEGER NOT NULL,
            motion INTEGER NOT NULL,
            severity TEXT NOT NULL,
            event TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature_c REAL NOT NULL,
            gas_raw INTEGER NOT NULL,
            motion INTEGER NOT NULL,
            severity TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event TEXT NOT NULL,
            severity TEXT NOT NULL,
            temperature_c REAL NOT NULL,
            gas_raw INTEGER NOT NULL,
            motion INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN',
            acknowledged_by TEXT,
            resolved_by TEXT
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER NOT NULL REFERENCES incidents(id),
            timestamp TEXT NOT NULL,
            recipient_username TEXT NOT NULL,
            recipient_role TEXT NOT NULL,
            message TEXT NOT NULL,
            channel TEXT NOT NULL DEFAULT 'DASHBOARD',
            delivery_status TEXT NOT NULL DEFAULT 'CREATED'
        );
        """)

        # Seed local demonstration accounts once. Change passwords before any real use.
        seeded = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
        if seeded == 0:
            demo_users = [
                ("resident", "Resident Demo", "Resident", "Resident123!", 0),
                ("caregiver", "Caregiver Demo", "Caregiver", "Caregiver123!", 0),
                ("responder", "Responder Demo", "Responder", "Responder123!", 1),
                ("admin", "Project Admin", "Admin", "Admin123!", 1),
            ]
            for username, display, role, password, responder_auth in demo_users:
                salt, pw_hash = hash_password(password)
                conn.execute(
                    """INSERT INTO users
                    (username, display_name, role, salt_hex, password_hash, responder_authorized)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (username, display, role, salt, pw_hash, responder_auth),
                )

def authenticate(username: str, password: str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND active = 1",
            (username.strip().lower(),),
        ).fetchone()
    if not row or not verify_password(password, row["salt_hex"], row["password_hash"]):
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "role": row["role"],
        "responder_authorized": bool(row["responder_authorized"]),
    }

def get_users():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, username, display_name, role, responder_authorized, active FROM users ORDER BY id"
        ).fetchall()]

def set_responder_permission(username: str, allowed: bool):
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET responder_authorized = ? WHERE username = ? AND role = 'Responder'",
            (int(allowed), username),
        )

def save_sensor_reading(data: dict, severity: str, event: str):
    timestamp = now_iso()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO sensor_readings
            (timestamp, temperature_c, gas_raw, motion, severity)
            VALUES (?, ?, ?, ?, ?)""",
            (timestamp, data["temperature_c"], data["gas_raw"], int(data["motion"]), severity),
        )
        conn.execute(
            """INSERT INTO current_state
            (id, timestamp, temperature_c, gas_raw, motion, severity, event)
            VALUES (1, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
            timestamp=excluded.timestamp,
            temperature_c=excluded.temperature_c,
            gas_raw=excluded.gas_raw,
            motion=excluded.motion,
            severity=excluded.severity,
            event=excluded.event""",
            (timestamp, data["temperature_c"], data["gas_raw"], int(data["motion"]), severity, event),
        )
    return timestamp

def save_incident(data: dict, result: dict) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO incidents
            (timestamp, event, severity, temperature_c, gas_raw, motion, status)
            VALUES (?, ?, ?, ?, ?, ?, 'OPEN')""",
            (now_iso(), result["event"], result["severity"],
             data["temperature_c"], data["gas_raw"], int(data["motion"])),
        )
        return int(cur.lastrowid)

def save_notification(incident_id: int, recipient: dict, message: str):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO notifications
            (incident_id, timestamp, recipient_username, recipient_role, message)
            VALUES (?, ?, ?, ?, ?)""",
            (incident_id, now_iso(), recipient["username"], recipient["role"], message),
        )

def get_current_state():
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM current_state WHERE id = 1").fetchone()
        return dict(row) if row else None

def get_readings(limit: int = 200):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM sensor_readings ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()][::-1]

def get_incidents():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM incidents ORDER BY id DESC"
        ).fetchall()]

def get_notifications_for_user(user: dict):
    with get_connection() as conn:
        if user["role"] == "Admin":
            rows = conn.execute("SELECT * FROM notifications ORDER BY id DESC").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM notifications WHERE recipient_username = ? ORDER BY id DESC",
                (user["username"],),
            ).fetchall()
        return [dict(r) for r in rows]

def update_incident_status(incident_id: int, status: str, username: str):
    if status not in ("ACKNOWLEDGED", "RESOLVED"):
        raise ValueError("Invalid incident status")
    with get_connection() as conn:
        if status == "ACKNOWLEDGED":
            conn.execute(
                """UPDATE incidents SET status = 'ACKNOWLEDGED', acknowledged_by = ?
                WHERE id = ? AND status = 'OPEN'""", (username, incident_id)
            )
        else:
            conn.execute(
                """UPDATE incidents SET status = 'RESOLVED', resolved_by = ?
                WHERE id = ? AND status IN ('OPEN','ACKNOWLEDGED')""",
                (username, incident_id),
            )

def get_authorized_incidents(user: dict):
    records = get_incidents()
    if user["role"] == "Admin":
        return records
    if user["role"] == "Responder":
        if not user["responder_authorized"]:
            return []
        return [r for r in records if r["severity"] == "CRITICAL"]
    # Resident and caregiver see the event summaries in this single-resident demo.
    return records
