"""
Alerting Service — watches stored readings and raises alerts.

Runs alongside the ingest service. It polls the database for new readings,
raises an alert when a reading breaches the temperature threshold, records
every alert in an `alerts` table (which the dashboard displays), and sends a
notification if a notification channel is configured.

Configuration (environment variables):
    ALERT_TEMP_THRESHOLD   temperature above which an alert fires (default 40)
    POLL_SECONDS           how often to check the database        (default 10)
    TELEGRAM_BOT_TOKEN     optional — enables Telegram notifications
    TELEGRAM_CHAT_ID       optional — the chat to send alerts to

If TELEGRAM_BOT_TOKEN is not set, alerts are printed to the console only, so
the service works out of the box with no accounts or secrets.

Never hard-code tokens in this file — set them in your environment.

Usage:
    python alerting.py
Stop with Ctrl+C.
"""

import os
import sqlite3
import time
from datetime import datetime, timezone

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DB_DIR, "sensors.db")

TEMP_THRESHOLD = float(os.environ.get("ALERT_TEMP_THRESHOLD", "40"))
POLL_SECONDS = float(os.environ.get("POLL_SECONDS", "10"))
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def init_alerts_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            reading_id  INTEGER,
            device      TEXT,
            temperature REAL,
            reason      TEXT,
            raised_at   TEXT
        )
        """
    )
    conn.commit()


def format_alert(reading: dict, threshold: float) -> str:
    """Human-readable alert message."""
    return (
        f"[ALERT] {reading['device']} temperature {reading['temperature']}°C "
        f"exceeds threshold {threshold}°C"
    )


def find_new_alerts(conn: sqlite3.Connection, threshold: float, last_id: int):
    """Return new readings above the threshold, and the highest id seen."""
    rows = conn.execute(
        "SELECT id, device, temperature, ts FROM readings "
        "WHERE id > ? AND temperature > ? ORDER BY id",
        (last_id, threshold),
    ).fetchall()
    highest = last_id
    for row in rows:
        highest = max(highest, row[0])
    return rows, highest


def record_alert(conn, reading_id, device, temperature, reason) -> None:
    conn.execute(
        "INSERT INTO alerts (reading_id, device, temperature, reason, raised_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (reading_id, device, temperature, reason, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def send_telegram(message: str) -> bool:
    """Send `message` over Telegram if configured. Returns True if sent."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(message)  # console fallback — no configuration needed
        return False

    # Imported lazily so the service runs even without the dependency installed.
    import json
    import urllib.request

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": message}).encode()
    request = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status == 200
    except Exception as e:  # network problems should not kill the service
        print(f"Telegram send failed ({e}) — alert still recorded")
        return False


def main():
    if not os.path.exists(DB_PATH):
        print(f"No database yet at {DB_PATH} — start ingest.py first.")
        return

    conn = sqlite3.connect(DB_PATH)
    init_alerts_table(conn)

    last_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM readings").fetchone()[0]
    print(f"Alerting service running — threshold {TEMP_THRESHOLD}°C, "
          f"polling every {POLL_SECONDS}s (Ctrl+C to stop)")

    try:
        while True:
            rows, last_id = find_new_alerts(conn, TEMP_THRESHOLD, last_id)
            for reading_id, device, temperature, _ts in rows:
                reading = {"device": device, "temperature": temperature}
                message = format_alert(reading, TEMP_THRESHOLD)
                record_alert(conn, reading_id, device, temperature, "high_temperature")
                send_telegram(message)
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
