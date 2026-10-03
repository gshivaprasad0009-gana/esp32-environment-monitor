"""
Tests for the ESP32 Environment Monitor pipeline.

These cover the parts that can be tested without hardware or a live MQTT
broker: the database layer, message handling, the simulator's payload format,
and the ML anomaly detector.

Run from the project root:

    pytest -q
"""

import importlib.util
import json
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


# --- database layer ---------------------------------------------------

def test_init_db_creates_readings_table(ingest):
    conn = ingest.init_db()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    assert ("readings",) in tables
    conn.close()


def test_on_message_stores_a_reading(ingest):
    conn = ingest.init_db()
    payload = json.dumps({
        "device": "esp32-01",
        "temperature": 27.5,
        "humidity": 61.0,
        "ts": "2026-09-30T10:00:00Z",
    }).encode()
    ingest.on_message(None, {"db": conn}, FakeMessage(payload))

    row = conn.execute(
        "SELECT device, temperature, humidity FROM readings"
    ).fetchone()
    assert row == ("esp32-01", 27.5, 61.0)
    conn.close()


def test_on_message_ignores_bad_payload(ingest):
    conn = ingest.init_db()
    ingest.on_message(None, {"db": conn}, FakeMessage(b"this is not json"))

    count = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
    assert count == 0  # a bad message is skipped, not stored
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

    assert set(reading) == {"device", "temperature", "humidity", "ts"}
    assert reading["device"] == "esp32-01"
    assert isinstance(reading["temperature"], float)
    assert isinstance(reading["humidity"], float)
    assert 0 < reading["humidity"] <= 100


def test_simulator_injects_a_spike_when_anomaly_triggers(monkeypatch):
    sim = load_module("sim_mod2", "simulator/sensor_simulator.py")
    # Force the anomaly branch: random() < ANOMALY_CHANCE
    monkeypatch.setattr(sim.random, "random", lambda: 0.0)

    reading = sim.make_reading()
    assert reading["temperature"] >= 45.0  # the spike range


def test_simulator_normal_reading_is_room_temperature(monkeypatch):
    sim = load_module("sim_mod3", "simulator/sensor_simulator.py")
    monkeypatch.setattr(sim.random, "random", lambda: 1.0)  # never anomalous

    reading = sim.make_reading()
    assert 20.0 <= reading["temperature"] <= 35.0


# --- ML anomaly detection ---------------------------------------------

def test_model_flags_a_temperature_spike(tmp_path, monkeypatch):
    train = load_module("train_mod", "ml/train_model.py")
    monkeypatch.setattr(train, "DB_DIR", str(tmp_path))
    monkeypatch.setattr(train, "DB_PATH", str(tmp_path / "missing.db"))  # use seed data
    monkeypatch.setattr(train, "MODEL_PATH", str(tmp_path / "model.joblib"))

    train.main()

    import joblib
    model = joblib.load(tmp_path / "model.joblib")
    predictions = model.predict(np.array([[27.0, 60.0], [50.0, 61.0]]))

    assert predictions[0] == 1    # normal reading stays normal
    assert predictions[1] == -1   # 50 C spike is flagged as an anomaly
