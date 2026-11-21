
import serial
import time
import json

from backend.database import (
    initialize_database,
    save_sensor_reading
)

WOKWI_PORT = "rfc2217://localhost:4000"
BAUD_RATE = 115200


def connect_wokwi():

    initialize_database()

    print("=" * 45)
    print("    PRIVASENSE X SENSOR RECEIVER")
    print("=" * 45)

    while True:
        try:
            print("\nConnecting to Wokwi...")

            with serial.serial_for_url(
                WOKWI_PORT,
                baudrate=BAUD_RATE,
                timeout=2
            ) as ser:

                print("CONNECTED TO WOKWI!")
                print("Saving live sensor data to database...\n")

                while True:

                    raw_data = ser.readline()

                    if not raw_data:
                        continue

                    try:
                        data = raw_data.decode(
                            "utf-8",
                            errors="replace"
                        ).strip()

                        if not data:
                            continue

                        # Convert JSON string into Python dictionary
                        sensor_data = json.loads(data)

                        # Check required sensor values
                        required = [
                            "temperature_c",
                            "gas_raw",
                            "motion"
                        ]

                        if not all(k in sensor_data for k in required):
                            continue

                        severity = sensor_data.get(
                            "severity", "NORMAL"
                        )

                        event = sensor_data.get(
                            "event", "Sensor update"
                        )

                        # Save readings to dashboard database
                        save_sensor_reading(
                            sensor_data,
                            severity,
                            event
                        )

                        print("LIVE SENSOR DATA:", sensor_data)
                        print("SAVED TO DASHBOARD DATABASE!")
                        print("-" * 45)

                    except json.JSONDecodeError:
                        print("Skipping non-JSON serial message")

                    except Exception as error:
                        print("DATA ERROR:", error)

        except KeyboardInterrupt:
            print("\nReceiver stopped.")
            break

        except Exception as error:
            print("\nCONNECTION ERROR:", error)
            print("Retrying in 3 seconds...")
            time.sleep(3)


if __name__ == "__main__":
    connect_wokwi()
