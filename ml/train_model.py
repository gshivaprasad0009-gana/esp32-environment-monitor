"""
ML Anomaly Detection — flags unusual sensor readings with Isolation Forest.

Trains on the stored readings (or a small seed set if the database is fresh),
saves the model to `data/model.joblib`, and scores the most recent readings
so the dashboard can highlight anomalies.

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

SEED_READINGS = [
    (26.1, 58.4), (26.5, 59.0), (27.0, 60.2), (26.8, 61.5), (27.3, 60.0),
    (28.0, 62.1), (27.5, 61.0), (26.9, 59.8), (27.8, 62.5), (28.2, 63.0),
    (27.1, 60.5), (26.6, 58.9), (28.5, 62.8), (27.9, 61.7), (26.4, 59.3),
]


def load_training_data() -> np.ndarray:
    """Load [temperature, humidity] pairs from the DB, or use seed data if empty."""
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT temperature, humidity FROM readings").fetchall()
        conn.close()
        if len(rows) >= 20:  # enough real data to train on
            print(f"Training on {len(rows)} readings from the database")
            return np.array(rows)

    print("Not enough stored readings yet — training on seed data")
    return np.array(SEED_READINGS)


def main():
    X = load_training_data()

    # contamination = expected fraction of anomalies. 0.1 works well for
    # both the simulator's 5% anomaly injection and small training sets.
    model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
    model.fit(X)

    os.makedirs(DB_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
