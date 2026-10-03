# ESP32 Environment Monitor — firmware

Firmware for the ESP32 sensor node. Reads temperature and humidity from a DHT22
and light level from an LDR, then publishes JSON readings over MQTT.

## Libraries needed (Arduino IDE)

Install these via **Sketch → Include Library → Manage Libraries**:

1. **PubSubClient** by Nick O'Leary
2. **DHT sensor library** by Adafruit
3. **Adafruit Unified Sensor** (required by the DHT library)
4. **ArduinoJson** by Benoit Blanchon

## Wiring

**DHT22 → ESP32**

| DHT22 | ESP32 |
|---|---|
| VCC | 3V3 |
| DATA | GPIO 4 |
| GND | GND |

**LDR (light sensor) → ESP32**

```
3V3 ── LDR ──┬── GPIO 34
             │
          10 kΩ
             │
            GND
```

GPIO 34 is an input-only ADC pin, which is exactly what a sensor needs.

## Setup

1. Open `esp32_environment_monitor.ino` in the Arduino IDE
2. Replace these values with your own:

   ```cpp
   const char* WIFI_SSID     = "YOUR_WIFI_NAME";
   const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
   const char* MQTT_BROKER   = "test.mosquitto.org";  // free public broker
   ```

3. Select your ESP32 board and port, then **Upload**
4. Open the Serial Monitor at **115200 baud** — readings should appear every 5 seconds

## Output format

Published to the topic `esp32/env-monitor/data`:

```json
{"device": "esp32-01", "temperature": 28.4, "humidity": 61.2, "light": 73.5}
```

The Python simulator (`simulator/sensor_simulator.py`) publishes the exact same
format, so the whole pipeline can be developed and tested without hardware.

## Changing the publish interval

Edit `PUBLISH_INTERVAL_MS` in the sketch (currently 5000 ms = 5 seconds).

## Parts list

| Component | Approx. price |
|---|---|
| ESP32 DevKit V1 | ₹300–500 |
| DHT22 temperature/humidity sensor module | ₹200–350 |
| LDR (photoresistor) + 10 kΩ resistor | ₹20–40 |
| Breadboard + jumper wires | ₹100–150 |
