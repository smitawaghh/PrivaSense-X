"""Command-line test runner for the PrivaSense X backend."""

from backend.database import initialize_database, get_incidents, get_notifications
from backend.sensor_simulator import SCENARIOS
from backend.service import process_scenario

def main():
    initialize_database()
    names = list(SCENARIOS.keys())

    while True:
        print("\n========== PRIVASENSE X BACKEND ==========")
        for i, name in enumerate(names, 1):
            print(f"{i}. {name}")
        print("7. View incident history")
        print("8. View notification history")
        print("9. Exit")

        choice = input("Choose an option: ").strip()

        if choice in [str(i) for i in range(1, 7)]:
            output = process_scenario(names[int(choice) - 1])
            print("\nSensor readings:", output["sensor_data"])
            print("Detection:", output["result"])
            if output["incident_id"]:
                print("Saved incident ID:", output["incident_id"])
            else:
                print("Normal conditions: no incident created.")
            print("\nPersonalized dashboard notifications:")
            for item in output["notifications"]:
                print(f"- {item['role']} ({item['username']}): {item['message']}")
        elif choice == "7":
            for item in get_incidents():
                print(item)
        elif choice == "8":
            for item in get_notifications():
                print(item)
        elif choice == "9":
            print("Backend stopped.")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
