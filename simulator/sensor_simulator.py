"""
Sensor Simulator — acts like the ESP32 when you don't have hardware yet.

Publishes realistic temperature/humidity readings to the MQTT topic
`esp32/env-monitor/data` in the exact same JSON format as the firmware.

Occasionally injects an "anomaly" (a sudden temperature spike) so the
ML anomaly detection has something interesting to catch.

Usage:
    python sensor_simulator.py
Stop with Ctrl+C.
"""

import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "esp32/env-monitor/data"
DEVICE_ID = "esp32-01"
INTERVAL_SECONDS = 5
ANOMALY_CHANCE = 0.05  # 5% of readings are anomalies


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT broker {BROKER}")
    else:
        print(f"Connection failed with code {rc}")


def make_reading() -> dict:
    """Generate one realistic (occasionally anomalous) sensor reading."""
    # Normal room conditions with small random walk
    temperature = round(random.uniform(24.0, 30.0), 1)
    humidity = round(random.uniform(50.0, 70.0), 1)

    # Inject an anomaly: sudden temperature spike
    if random.random() < ANOMALY_CHANCE:
        temperature = round(random.uniform(45.0, 55.0), 1)

    return {
        "device": DEVICE_ID,
        "temperature": temperature,
        "humidity": humidity,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    print(f"Simulating sensor readings every {INTERVAL_SECONDS}s on '{TOPIC}' (Ctrl+C to stop)")
    try:
        while True:
            reading = make_reading()
            client.publish(TOPIC, json.dumps(reading))
            print(f"Published: {reading}")
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
