"""
MQTT Ingest Service — receives sensor readings and stores them in SQLite.

Subscribes to the MQTT topic the ESP32 (or the simulator) publishes on,
parses the JSON payload, and inserts each reading into `data/sensors.db`.

Usage:
    python ingest.py
Stop with Ctrl+C.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "esp32/env-monitor/data"

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DB_DIR, "sensors.db")


def init_db() -> sqlite3.Connection:
    """Create the database and readings table if they don't exist."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS readings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            device      TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity    REAL NOT NULL,
            ts          TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Connected to MQTT broker {BROKER}")
        client.subscribe(TOPIC)
        print(f"Subscribed to '{TOPIC}'")
    else:
        print(f"Connection failed with code {rc}")


def on_message(client, userdata, msg):
    """Handle one incoming sensor reading."""
    conn = userdata["db"]
    try:
        reading = json.loads(msg.payload.decode())
        conn.execute(
            "INSERT INTO readings (device, temperature, humidity, ts) VALUES (?, ?, ?, ?)",
            (
                reading.get("device", "unknown"),
                float(reading["temperature"]),
                float(reading["humidity"]),
                reading.get("ts", datetime.now(timezone.utc).isoformat()),
            ),
        )
        conn.commit()
        print(f"Stored: {reading}")
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Skipping bad message ({e}): {msg.payload!r}")


def main():
    conn = init_db()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.user_data_set({"db": conn})
    client.connect(BROKER, PORT, keepalive=60)

    print("Ingest service running — press Ctrl+C to stop.")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
