# PrivaSense X

Privacy-first, role-aware assistive event intelligence prototype.

## What is included

- Python sensor simulator for temperature, gas and PIR motion.
- Event detection with configurable demonstration thresholds.
- SQLite database for sensor readings, current state, incidents and notifications.
- Role-specific dashboard notification generation.
- Streamlit dashboard with demo login, overview, monitoring, incident history,
  personalized alerts and an admin permission page.

## Important prototype limitations

- Sensor values are simulated in software. This project does not automatically
  receive live values from Tinkercad.
- The threshold values are illustrative and are NOT certified safety limits.
- The included login is for a local student demonstration, not production use.
- Dashboard notifications are stored in SQLite; Telegram/SMS/email delivery is
  not implemented.
- Do not rely on this prototype for real emergency monitoring or dispatch.

## Requirements

- Windows 10/11
- Python 3.10 or newer
- VS Code (optional but recommended)

## Setup on Windows PowerShell

Open a terminal in the `PrivaSenseX` project folder.

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

## Run the backend command-line test

From the project root:

```powershell
py -m backend.run_backend
```

Choose scenarios 1-6 to simulate events, 7 to view incident history,
8 to view notification history, and 9 to exit.

## Run the Streamlit dashboard

From the project root:

```powershell
py -m streamlit run dashboard/app.py
```

The browser should open the dashboard. If it does not, use the local URL
printed in the terminal (usually http://localhost:8501).

## Demo accounts

These accounts are created automatically on the first database initialization:

| Role | Username | Password |
|---|---|---|
| Resident | `resident` | `Resident123!` |
| Caregiver | `caregiver` | `Caregiver123!` |
| Responder | `responder` | `Responder123!` |
| Admin | `admin` | `Admin123!` |

Change these passwords before any real deployment. The passwords are hashed
in SQLite, but the initial credentials are intentionally simple for a classroom
demo. Do not expose this demo application to the public internet.

## Project structure

```text
PrivaSenseX/
├── backend/
│   ├── __init__.py
│   ├── config.py
│   ├── sensor_simulator.py
│   ├── event_detector.py
│   ├── database.py
│   ├── alert_manager.py
│   ├── service.py
│   └── run_backend.py
├── dashboard/
│   ├── __init__.py
│   ├── auth.py
│   └── app.py
├── data/
│   └── privasense.db       # created automatically
├── requirements.txt
└── README.md
```

## Tinkercad integration note

Tinkercad Circuits is used as a separate circuit simulation in this prototype.
It does not provide a direct automatic local Python data feed. The software
simulator currently supplies equivalent demonstration readings. A future
integration could use a real Arduino serial connection or another supported
data bridge, with a hardware device or suitable simulator interface.

## Reset the demo database

Stop the app, then delete `data/privasense.db`. It will be recreated with
the demo accounts and empty history on the next run. This permanently deletes
the locally stored demo history.
