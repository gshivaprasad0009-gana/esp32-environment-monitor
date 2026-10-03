"""
ML Anomaly Detection — flags unusual sensor readings with Isolation Forest.

Trains on the stored readings (or a small seed set if the database is fresh)
and saves the model to `data/model.joblib`. The dashboard uses the model's
anomaly scores, so the sensitivity can be adjusted there without retraining.

Configuration (environment variables, all optional):
    ANOMALY_CONTAMINATION   expected fraction of anomalies (default 0.1)

Usage:
    python train_model.py
"""

import os
import sqlite3

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DB_DIR, "sensors.db")
MODEL_PATH = os.path.join(DB_DIR, "model.joblib")

CONTAMINATION = float(os.environ.get("ANOMALY_CONTAMINATION", "0.1"))

# Feature order used by both training and the dashboard: [temp, humidity, light]
FEATURES = ["temperature", "humidity", "light"]


def _seed_readings(n: int = 150, seed: int = 7) -> np.ndarray:
    """A deterministic synthetic set of normal readings.

    Isolation Forest needs a reasonable sample of "normal" before it can judge
    what is unusual — a handful of points is not enough. These are generated
    from a fixed seed so the bootstrap behaviour is reproducible, and they are
    replaced by real readings as soon as the database has collected enough.
    """
    rng = np.random.default_rng(seed)
    temperature = rng.normal(27.0, 1.5, n)
    humidity = np.clip(rng.normal(60.0, 4.0, n), 40, 80)
    light = np.clip(rng.normal(60.0, 10.0, n), 5, 95)
    return np.column_stack([temperature, humidity, light])


SEED_READINGS = _seed_readings()


def load_training_data() -> np.ndarray:
    """Load [temp, humidity, light] rows from the DB, or use seed data if empty."""
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT temperature, humidity, COALESCE(light, 50.0) FROM readings"
        ).fetchall()
        conn.close()
        if len(rows) >= 20:  # enough real data to train on
            print(f"Training on {len(rows)} readings from the database")
            return np.array(rows, dtype=float)

    print("Not enough stored readings yet — training on seed data")
    return np.array(SEED_READINGS, dtype=float)


def main():
    X = load_training_data()

    model = IsolationForest(
        n_estimators=100, contamination=CONTAMINATION, random_state=42
    )
    model.fit(X)

    os.makedirs(DB_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH} (contamination={CONTAMINATION})")


if __name__ == "__main__":
    main()
