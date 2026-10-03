"""
Tests for the ESP32 Environment Monitor pipeline.

These cover the parts that can be tested without hardware or a live MQTT
broker: the database layer and its migration, message handling, the
simulator's payload format and configuration, the ML anomaly detector, the
dashboard's pure logic, and the alerting service.

Run from the project root:

    pytest -q
"""

import importlib.util
import json
import os
import sqlite3
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relpath):
    """Load a module from a file path (the project folders are not packages)."""
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeMessage:
    """Minimal stand-in for a paho MQTT message."""

    def __init__(self, payload: bytes):
        self.payload = payload


@pytest.fixture
def ingest(tmp_path, monkeypatch):
    """The ingest module, with its database pointed at a temp directory."""
    module = load_module("ingest_mod", "backend/ingest.py")
    monkeypatch.setattr(module, "DB_DIR", str(tmp_path))
    monkeypatch.setattr(module, "DB_PATH", str(tmp_path / "sensors.db"))
    return module


# --- ingest: database layer and migration -----------------------------

def test_init_db_creates_readings_table(ingest):
    conn = ingest.init_db()
    columns = {row[1] for row in conn.execute("PRAGMA table_info(readings)")}
    assert {"device", "temperature", "humidity", "light", "ts"} <= columns
    conn.close()


def test_init_db_adds_light_column_to_an_old_database(ingest):
    # Simulate a v1.0 database that predates the light sensor.
    os.makedirs(str(ingest.DB_DIR), exist_ok=True)
    old = sqlite3.connect(ingest.DB_PATH)
    old.execute(
        "CREATE TABLE readings (id INTEGER PRIMARY KEY AUTOINCREMENT, device TEXT,"
        " temperature REAL, humidity REAL, ts TEXT)"
    )
    old.commit()
    old.close()

    conn = ingest.init_db()  # must migrate in place, not fail
    columns = {row[1] for row in conn.execute("PRAGMA table_info(readings)")}
    assert "light" in columns
    conn.close()


def test_on_message_stores_a_reading_with_light(ingest):
    conn = ingest.init_db()
    payload = json.dumps({
        "device": "esp32-01",
        "temperature": 27.5,
        "humidity": 61.0,
        "light": 73.5,
        "ts": "2026-09-30T10:00:00Z",
    }).encode()
    ingest.on_message(None, {"db": conn}, FakeMessage(payload))

    row = conn.execute(
        "SELECT device, temperature, humidity, light FROM readings"
    ).fetchone()
    assert row == ("esp32-01", 27.5, 61.0, 73.5)
    conn.close()


def test_on_message_accepts_a_reading_without_light(ingest):
    # An older sensor node that does not report light should still work.
    conn = ingest.init_db()
    payload = json.dumps({
        "device": "esp32-02", "temperature": 26.0, "humidity": 55.0,
    }).encode()
    ingest.on_message(None, {"db": conn}, FakeMessage(payload))

    row = conn.execute("SELECT device, light FROM readings").fetchone()
    assert row == ("esp32-02", None)
    conn.close()


def test_on_message_ignores_bad_payload(ingest):
    conn = ingest.init_db()
    ingest.on_message(None, {"db": conn}, FakeMessage(b"this is not json"))
    count = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
    assert count == 0
    conn.close()


def test_on_message_ignores_missing_fields(ingest):
    conn = ingest.init_db()
    ingest.on_message(None, {"db": conn}, FakeMessage(b'{"device": "esp32-01"}'))
    count = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
    assert count == 0
    conn.close()


# --- simulator --------------------------------------------------------

def test_simulator_reading_has_expected_shape():
    sim = load_module("sim_mod", "simulator/sensor_simulator.py")
    reading = sim.make_reading()

    assert set(reading) == {"device", "temperature", "humidity", "light", "ts"}
    assert reading["device"] == "esp32-01"
    assert isinstance(reading["temperature"], float)
    assert isinstance(reading["humidity"], float)
    assert 0 <= reading["light"] <= 100
    assert 0 < reading["humidity"] <= 100


def test_simulator_injects_a_spike_when_anomaly_triggers(monkeypatch):
    sim = load_module("sim_mod2", "simulator/sensor_simulator.py")
    monkeypatch.setattr(sim.random, "random", lambda: 0.0)  # force anomaly
    reading = sim.make_reading()
    assert reading["temperature"] >= 45.0


def test_simulator_normal_reading_is_room_temperature(monkeypatch):
    sim = load_module("sim_mod3", "simulator/sensor_simulator.py")
    monkeypatch.setattr(sim.random, "random", lambda: 1.0)  # never anomalous
    reading = sim.make_reading()
    assert 20.0 <= reading["temperature"] <= 35.0


def test_simulator_interval_is_configurable(monkeypatch):
    monkeypatch.setenv("PUBLISH_INTERVAL_SECONDS", "42")
    sim = load_module("sim_mod4", "simulator/sensor_simulator.py")
    assert sim.INTERVAL_SECONDS == 42.0


# --- ML anomaly detection ---------------------------------------------

def test_model_flags_a_temperature_spike(tmp_path, monkeypatch):
    train = load_module("train_mod", "ml/train_model.py")
    monkeypatch.setattr(train, "DB_DIR", str(tmp_path))
    monkeypatch.setattr(train, "DB_PATH", str(tmp_path / "missing.db"))
    monkeypatch.setattr(train, "MODEL_PATH", str(tmp_path / "model.joblib"))

    train.main()

    import joblib
    model = joblib.load(tmp_path / "model.joblib")
    predictions = model.predict(np.array([[27.0, 60.0, 55.0], [50.0, 61.0, 55.0]]))

    assert predictions[0] == 1
    assert predictions[1] == -1


def test_model_trains_on_three_features(tmp_path, monkeypatch):
    train = load_module("train_mod2", "ml/train_model.py")
    monkeypatch.setattr(train, "DB_DIR", str(tmp_path))
    monkeypatch.setattr(train, "DB_PATH", str(tmp_path / "missing.db"))
    monkeypatch.setattr(train, "MODEL_PATH", str(tmp_path / "model.joblib"))
    train.main()

    import joblib
    model = joblib.load(tmp_path / "model.joblib")
    assert model.n_features_in_ == 3
    assert train.FEATURES == ["temperature", "humidity", "light"]


# --- dashboard logic --------------------------------------------------

@pytest.fixture
def dash():
    return load_module("dash_mod", "backend/dashboard.py")


def test_to_fahrenheit(dash):
    assert dash.to_fahrenheit(0) == 32.0
    assert dash.to_fahrenheit(100) == 212.0


def test_flag_anomalies_without_a_model_marks_nothing(dash):
    import pandas as pd
    df = pd.DataFrame({
        "temperature": [27.0, 28.0], "humidity": [60.0, 61.0], "light": [50.0, 51.0],
    })
    result = dash.flag_anomalies(df, None, 10)
    assert not result["anomaly"].any()


def test_higher_sensitivity_flags_more_readings(dash, tmp_path, monkeypatch):
    import joblib
    import pandas as pd

    train = load_module("train_mod3", "ml/train_model.py")
    monkeypatch.setattr(train, "DB_DIR", str(tmp_path))
    monkeypatch.setattr(train, "DB_PATH", str(tmp_path / "missing.db"))
    monkeypatch.setattr(train, "MODEL_PATH", str(tmp_path / "model.joblib"))
    train.main()  # trains on seed data, into the temp directory
    model = joblib.load(train.MODEL_PATH)

    df = pd.DataFrame({
        "temperature": [27.0, 27.5, 28.0, 26.5, 27.2, 50.0],
        "humidity": [60.0, 61.0, 62.0, 59.0, 60.5, 61.0],
        "light": [50.0, 52.0, 54.0, 48.0, 51.0, 55.0],
    })
    low = dash.flag_anomalies(df, model, 1)["anomaly"].sum()
    high = dash.flag_anomalies(df, model, 30)["anomaly"].sum()
    assert high >= low


# --- alerting ---------------------------------------------------------

def _alerting_with_temp_db(tmp_path, monkeypatch):
    module = load_module("alert_mod", "backend/alerting.py")
    monkeypatch.setattr(module, "DB_DIR", str(tmp_path))
    monkeypatch.setattr(module, "DB_PATH", str(tmp_path / "sensors.db"))
    monkeypatch.setattr(module, "TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setattr(module, "TELEGRAM_CHAT_ID", "")
    return module


def _make_readings_db(path):
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE readings (id INTEGER PRIMARY KEY AUTOINCREMENT, device TEXT,"
        " temperature REAL, humidity REAL, light REAL, ts TEXT)"
    )
    conn.executemany(
        "INSERT INTO readings (device, temperature, humidity, light, ts) VALUES (?,?,?,?,?)",
        [
            ("esp32-01", 27.0, 60.0, 50.0, "2026-09-30T10:00:00Z"),
            ("esp32-01", 52.0, 61.0, 55.0, "2026-09-30T10:00:05Z"),
            ("esp32-01", 28.0, 59.0, 51.0, "2026-09-30T10:00:10Z"),
        ],
    )
    conn.commit()
    return conn


def test_format_alert_names_the_device_and_threshold():
    alert = load_module("alert_fmt", "backend/alerting.py")
    message = alert.format_alert({"device": "esp32-01", "temperature": 52.0}, 40.0)
    assert "esp32-01" in message
    assert "52.0" in message
    assert "40.0" in message


def test_find_new_alerts_only_returns_readings_above_threshold(tmp_path, monkeypatch):
    alerting = _alerting_with_temp_db(tmp_path, monkeypatch)
    conn = _make_readings_db(alerting.DB_PATH)

    rows, highest = alerting.find_new_alerts(conn, threshold=40.0, last_id=0)
    assert len(rows) == 1                 # only the 52 °C spike
    assert rows[0][2] == 52.0
    assert highest == 2

    # Nothing new after the spike has been seen
    rows_again, _ = alerting.find_new_alerts(conn, threshold=40.0, last_id=highest)
    assert rows_again == []
    conn.close()


def test_record_alert_writes_to_the_alerts_table(tmp_path, monkeypatch):
    alerting = _alerting_with_temp_db(tmp_path, monkeypatch)
    conn = _make_readings_db(alerting.DB_PATH)
    alerting.init_alerts_table(conn)
    alerting.record_alert(conn, 2, "esp32-01", 52.0, "high_temperature")

    row = conn.execute("SELECT device, temperature, reason FROM alerts").fetchone()
    assert row == ("esp32-01", 52.0, "high_temperature")
    conn.close()


def test_send_telegram_falls_back_to_console_without_configuration(capsys):
    alerting = load_module("alert_tg", "backend/alerting.py")
    sent = alerting.send_telegram("test message")
    assert sent is False
    assert "test message" in capsys.readouterr().out
