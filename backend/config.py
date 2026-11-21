from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "privasense.db"

# Demonstration thresholds only. These are NOT certified safety limits.
TEMP_WARNING_C = 45.0
TEMP_CRITICAL_C = 60.0
GAS_CRITICAL_RAW = 400

APP_NAME = "PrivaSense X"
