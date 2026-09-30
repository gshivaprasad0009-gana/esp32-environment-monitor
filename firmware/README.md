# esp32-environment-monitor

Firmware for the ESP32 + DHT22 sensor.
Reads temperature and humidity, and publishes JSON readings over MQTT.

## Libraries needed (Arduino IDE)

1. **PubSubClient** by Nick O'Leary — Sketch > Include Library > Manage Libraries > search "PubSubClient"
2. **DHT sensor library** by Adafruit (install "Adafruit Unified Sensor" too)

## Setup

1. Open `esp32_environment_monitor.ino` in the Arduino IDE
2. Replace these values with your own:

   ```cpp
   const char* WIFI_SSID     = "YOUR_WIFI_NAME";
   const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
   const char* MQTT_BROKER   = "test.mosquitto.org";  // free public broker
   ```

3. Select your ESP32 board and port, then Upload
4. Open the Serial Monitor (115200 baud) — you should see readings being published every 5 seconds

## How it works

```
[DHT22 sensor] -> [ESP32] -> WiFi -> MQTT broker -> [backend ingest] -> [SQLite] -> [Streamlit dashboard]
```

The JSON message published to topic `esp32/env-monitor/data` looks like:

```json
{"device": "esp32-01", "temperature": 28.4, "humidity": 61.2, "ts": "2026-09-30T10:00:00Z"}
```

The included Python simulator (`simulator/sensor_simulator.py`) publishes the
exact same messages, so you can develop and test the whole pipeline without hardware.
