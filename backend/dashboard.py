"""
Live Dashboard — Streamlit app showing sensor readings and ML anomaly flags.

Shows the latest readings, live-updating charts, and highlights readings the
Isolation Forest model considers anomalous.

Usage:
    streamlit run dashboard.py
"""

import os
import sqlite3

import joblib
import pandas as pd
import streamlit as st

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DB_DIR, "sensors.db")
MODEL_PATH = os.path.join(DB_DIR, "model.joblib")

REFRESH_SECONDS = 5


@st.cache_resource
def load_model():
    """Load the trained Isolation Forest (if it exists)."""
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None


def load_readings() -> pd.DataFrame:
    """Read all stored sensor readings into a DataFrame."""
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=["ts", "device", "temperature", "humidity"])
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT ts, device, temperature, humidity FROM readings ORDER BY id", conn
    )
    conn.close()
    return df


def flag_anomalies(df: pd.DataFrame, model) -> pd.DataFrame:
    """Use the ML model to mark anomalous readings (model predicts -1)."""
    df = df.copy()
    if model is not None and len(df) > 0:
        X = df[["temperature", "humidity"]].values
        df["anomaly"] = model.predict(X) == -1
    else:
        df["anomaly"] = False
    return df


def main():
    st.set_page_config(page_title="ESP32 Environment Monitor", page_icon="🌡️", layout="wide")
    st.title("🌡️ ESP32 Environment Monitor")
    st.caption("Live sensor readings with ML anomaly detection")

    df = flag_anomalies(load_readings(), load_model())

    if df.empty:
        st.info(
            "No readings yet. Start the pipeline first:\n\n"
            "1. `python backend/ingest.py` — receive and store readings\n"
            "2. `python simulator/sensor_simulator.py` — generate readings\n"
            "3. `python ml/train_model.py` — train the anomaly detector"
        )
        return

    # --- Key metrics -----------------------------------------------------
    latest = df.iloc[-1]
    anomaly_count = int(df["anomaly"].sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌡️ Temperature", f"{latest['temperature']} °C")
    col2.metric("💧 Humidity", f"{latest['humidity']} %")
    col3.metric("📊 Total readings", len(df))
    col4.metric("🚨 Anomalies", anomaly_count)

    # --- Charts ----------------------------------------------------------
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce", utc=True)

    chart_col, anomaly_col = st.columns([3, 1])
    with chart_col:
        st.subheader("📈 Temperature & Humidity over time")
        st.line_chart(df.set_index("ts")[["temperature", "humidity"]])

    with anomaly_col:
        st.subheader("🚨 Anomalous readings")
        anomalies = df[df["anomaly"]].tail(10)
        if anomalies.empty:
            st.success("No anomalies detected — everything looks normal.")
        else:
            st.dataframe(
                anomalies[["ts", "temperature", "humidity"]],
                use_container_width=True,
                hide_index=True,
            )

    # --- Raw data --------------------------------------------------------
    with st.expander("🗂️ Recent raw readings"):
        st.dataframe(df.tail(50), use_container_width=True, hide_index=True)

    st.caption(f"Auto-refreshing every {REFRESH_SECONDS}s")
    st.empty()  # placeholder to keep the layout stable
    import time
    time.sleep(REFRESH_SECONDS)
    st.rerun()


if __name__ == "__main__":
    main()
