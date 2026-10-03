"""
Live Dashboard — Streamlit app showing sensor readings, ML anomaly flags and
recent alerts.

Shows the latest readings, live-updating charts, a panel of the readings the
Isolation Forest considers anomalous, and the alert history. The temperature
unit and the anomaly sensitivity are both adjustable from the sidebar.

Usage:
    streamlit run backend/dashboard.py
"""

import os
import sqlite3
import time

import joblib
import numpy as np
import pandas as pd
import streamlit as st

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DB_DIR, "sensors.db")
MODEL_PATH = os.path.join(DB_DIR, "model.joblib")

REFRESH_SECONDS = 5
FEATURES = ["temperature", "humidity", "light"]


@st.cache_resource
def load_model():
    """Load the trained Isolation Forest (if it exists)."""
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None


def load_readings() -> pd.DataFrame:
    """Read all stored sensor readings into a DataFrame."""
    columns = ["ts", "device", "temperature", "humidity", "light"]
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=columns)
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT ts, device, temperature, humidity, COALESCE(light, 50.0) AS light "
        "FROM readings ORDER BY id",
        conn,
    )
    conn.close()
    return df


def load_alerts() -> pd.DataFrame:
    """Read the alert history, if the alerting service has written any."""
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=["raised_at", "device", "temperature", "reason"])
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            "SELECT raised_at, device, temperature, reason FROM alerts "
            "ORDER BY id DESC LIMIT 20",
            conn,
        )
    except pd.errors.DatabaseError:
        df = pd.DataFrame(columns=["raised_at", "device", "temperature", "reason"])
    conn.close()
    return df


def flag_anomalies(df: pd.DataFrame, model, sensitivity: float) -> pd.DataFrame:
    """Mark anomalous readings using the model's anomaly scores.

    `sensitivity` is the percentage of readings to treat as anomalies (1-30).
    Using a percentile of the scores means the sensitivity can be changed from
    the dashboard without retraining the model.
    """
    df = df.copy()
    if model is None or df.empty:
        df["anomaly"] = False
        return df

    X = df[FEATURES].fillna(50.0).values
    scores = model.decision_function(X)      # lower score = more anomalous
    cutoff = np.percentile(scores, sensitivity)
    df["anomaly"] = scores < cutoff
    return df


def to_fahrenheit(celsius: float) -> float:
    return round(celsius * 9 / 5 + 32, 1)


def main():
    st.set_page_config(page_title="ESP32 Environment Monitor", page_icon="🌡️", layout="wide")
    st.title("🌡️ ESP32 Environment Monitor")
    st.caption("Live sensor readings with ML anomaly detection")

    with st.sidebar:
        st.header("⚙️ Settings")
        unit = st.radio("Temperature unit", ["°C", "°F"], horizontal=True)
        sensitivity = st.slider(
            "Anomaly sensitivity (% of readings flagged)", 1, 30, 10,
            help="Higher values flag more readings as anomalous.",
        )

    df = flag_anomalies(load_readings(), load_model(), sensitivity)
    alerts = load_alerts()

    if df.empty:
        st.info(
            "No readings yet. Start the pipeline first:\n\n"
            "1. `python backend/ingest.py` — receive and store readings\n"
            "2. `python simulator/sensor_simulator.py` — generate readings\n"
            "3. `python ml/train_model.py` — train the anomaly detector\n"
            "4. `python backend/alerting.py` — raise alerts on high temperature"
        )
        return

    def show_temp(celsius: float) -> str:
        return f"{to_fahrenheit(celsius)} °F" if unit == "°F" else f"{celsius} °C"

    # --- Key metrics -----------------------------------------------------
    latest = df.iloc[-1]
    anomaly_count = int(df["anomaly"].sum())

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🌡️ Temperature", show_temp(latest["temperature"]))
    col2.metric("💧 Humidity", f"{latest['humidity']} %")
    col3.metric("💡 Light", f"{latest['light']} %")
    col4.metric("📊 Total readings", len(df))
    col5.metric("🚨 Anomalies", anomaly_count)

    # --- Charts ----------------------------------------------------------
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce", utc=True)
    chart_df = df.set_index("ts")[["temperature", "humidity", "light"]].copy()
    if unit == "°F":
        chart_df["temperature"] = chart_df["temperature"] * 9 / 5 + 32

    chart_col, anomaly_col = st.columns([3, 1])
    with chart_col:
        st.subheader("📈 Readings over time")
        st.line_chart(chart_df)

    with anomaly_col:
        st.subheader("🚨 Anomalous readings")
        anomalies = df[df["anomaly"]].tail(10)
        if anomalies.empty:
            st.success("No anomalies at this sensitivity.")
        else:
            display = anomalies[["ts", "temperature", "humidity", "light"]].copy()
            if unit == "°F":
                display["temperature"] = display["temperature"].map(to_fahrenheit)
            st.dataframe(display, use_container_width=True, hide_index=True)

    # --- Alerts ----------------------------------------------------------
    st.subheader("🔔 Recent alerts")
    if alerts.empty:
        st.caption(
            "No alerts yet. Run `python backend/alerting.py` to watch for "
            "high-temperature readings."
        )
    else:
        st.dataframe(alerts, use_container_width=True, hide_index=True)

    # --- Raw data --------------------------------------------------------
    with st.expander("🗂️ Recent raw readings"):
        st.dataframe(df.tail(50), use_container_width=True, hide_index=True)

    st.caption(f"Auto-refreshing every {REFRESH_SECONDS}s")
    time.sleep(REFRESH_SECONDS)
    st.rerun()


if __name__ == "__main__":
    main()
