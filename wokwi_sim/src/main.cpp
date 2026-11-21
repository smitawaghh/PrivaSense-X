#include <Arduino.h>
#include <math.h>

// PrivaSense X - Wokwi sensor simulation
// Wokwi NTC temperature sensor -> A0
// Wokwi MQ2 gas sensor AOUT -> A1
// Wokwi PIR OUT -> D2

const int TEMP_PIN = A0;
const int GAS_PIN = A1;
const int PIR_PIN = 2;

const float BETA = 3950.0;
const float TEMP_WARNING_C = 45.0;
const float TEMP_CRITICAL_C = 60.0;
const int GAS_CRITICAL_RAW = 400;

float readTemperatureC()
{
  int analogValue = analogRead(TEMP_PIN);

  // Guard against invalid endpoint readings.
  if (analogValue <= 0)
    analogValue = 1;
  if (analogValue >= 1023)
    analogValue = 1022;

  // Formula for Wokwi's NTC module with 10K thermistor, beta=3950.
  float celsius =
      1.0 / (log(1.0 / (1023.0 / analogValue - 1.0)) / BETA + 1.0 / 298.15) - 273.15;

  return celsius;
}

void setup()
{
  pinMode(PIR_PIN, INPUT);
  Serial.begin(115200);
  delay(1000);
  Serial.println("{\"device\":\"PrivaSenseX\",\"status\":\"started\"}");
}

void loop()
{
  float temperatureC = readTemperatureC();
  int gasRaw = analogRead(GAS_PIN);
  bool motion = digitalRead(PIR_PIN) == HIGH;

  const char *severity = "NORMAL";
  const char *eventName = "Normal environmental conditions";

  bool criticalTemp = temperatureC >= TEMP_CRITICAL_C;
  bool warningTemp = temperatureC >= TEMP_WARNING_C;
  bool gasAlert = gasRaw >= GAS_CRITICAL_RAW;

  if (criticalTemp && gasAlert)
  {
    severity = "CRITICAL";
    eventName = "Combined temperature and gas alert";
  }
  else if (criticalTemp)
  {
    severity = "CRITICAL";
    eventName = "Critical temperature alert";
  }
  else if (gasAlert)
  {
    severity = "CRITICAL";
    eventName = "Gas alert";
  }
  else if (warningTemp)
  {
    severity = "WARNING";
    eventName = "High temperature warning";
  }

  // One JSON object per line: easy for Python to parse.
  Serial.print("{\"device\":\"PrivaSenseX\"");
  Serial.print(",\"temperature_c\":");
  Serial.print(temperatureC, 2);
  Serial.print(",\"gas_raw\":");
  Serial.print(gasRaw);
  Serial.print(",\"motion\":");
  Serial.print(motion ? "true" : "false");
  Serial.print(",\"severity\":\"");
  Serial.print(severity);
  Serial.print("\",\"event\":\"");
  Serial.print(eventName);
  Serial.println("\"}");

  delay(2000);
}
