"""
Sensor Simulator — acts like the ESP32 when you don't have hardware yet.

Publishes realistic temperature, humidity and light readings to the MQTT topic
`esp32/env-monitor/data` in the exact same JSON format as the firmware.

Occasionally injects an "anomaly" (a sudden temperature spike) so the ML
anomaly detection has something interesting to catch.

Configuration (environment variables, all optional):
    PUBLISH_INTERVAL_SECONDS   seconds between readings      (default 5)
    MQTT_BROKER                broker hostname               (default test.mosquitto.org)
    ANOMALY_CHANCE             fraction of readings that are spikes (default 0.05)

Usage:
    python sensor_simulator.py
Stop with Ctrl+C.
"""

import json
import os
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

BROKER = os.environ.get("MQTT_BROKER", "test.mosquitto.org")
PORT = int(os.environ.get("MQTT_PORT", "1883"))
TOPIC = "esp32/env-monitor/data"
DEVICE_ID = "esp32-01"
INTERVAL_SECONDS = float(os.environ.get("PUBLISH_INTERVAL_SECONDS", "5"))
ANOMALY_CHANCE = float(os.environ.get("ANOMALY_CHANCE", "0.05"))

# A slow day/night cycle for the light reading, so the chart looks realistic.
_start = time.time()


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Connected to MQTT broker {BROKER}")
    else:
        print(f"Connection failed with code {rc}")


def current_light() -> float:
    """Light level as a percentage, drifting on a slow cycle plus noise."""
    elapsed = time.time() - _start
    base = 50 + 45 * abs(((elapsed / 60) % 2) - 1)   # 5% .. 95% over ~2 minutes
    return round(max(0.0, min(100.0, base + random.uniform(-4, 4))), 1)


def make_reading() -> dict:
    """Generate one realistic (occasionally anomalous) sensor reading."""
    temperature = round(random.uniform(24.0, 30.0), 1)
    humidity = round(random.uniform(50.0, 70.0), 1)

    # Inject an anomaly: sudden temperature spike
    if random.random() < ANOMALY_CHANCE:
        temperature = round(random.uniform(45.0, 55.0), 1)

    return {
        "device": DEVICE_ID,
        "temperature": temperature,
        "humidity": humidity,
        "light": current_light(),
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    print(f"Simulating readings every {INTERVAL_SECONDS}s on '{TOPIC}' (Ctrl+C to stop)")
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
