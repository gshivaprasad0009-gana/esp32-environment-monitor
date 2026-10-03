# Roadmap

Where this project is going, in the order it should be built. Each level is a
working milestone — finish it, commit it, move on.

## ✅ Done

- ESP32 firmware: DHT22 readings published over MQTT
- Hardware-free simulator publishing the same message format
- Ingest service: MQTT → SQLite
- Live Streamlit dashboard with charts and metrics
- Isolation Forest anomaly detection
- Unit tests for the pipeline logic
- MIT license and this roadmap

## Level 1 — Small tweaks

Low-risk changes that build familiarity with the code.

- [ ] Make the publish interval configurable (currently 5 seconds)
- [ ] Add a Celsius / Fahrenheit toggle to the dashboard
- [ ] Make the anomaly sensitivity adjustable from the dashboard

## Level 2 — More sensors

- [ ] Add a second sensor (air quality or light) to the firmware and pipeline
- [ ] Show the new reading as its own chart on the dashboard

## Level 3 — Alerts

Turn monitoring into alerting.

- [ ] Send a notification (email or Telegram) when an anomaly is detected
- [ ] Add a configurable threshold so obvious spikes alert instantly
- [ ] Add a "last alert" panel to the dashboard

## Level 4 — Real hardware

- [ ] Order an ESP32 DevKit V1 and a DHT22 module
- [ ] Flash the firmware and confirm real readings reach the dashboard
- [ ] Document the wiring with photos

## Level 5 — Migrate to AWS

The flagship step: move the whole pipeline onto AWS.

- [ ] Replace the public MQTT broker with **AWS IoT Core**
- [ ] Replace the ingest script with a **Lambda** function
- [ ] Replace SQLite with **DynamoDB** (or Timestream for time-series data)
- [ ] Host the dashboard on **EC2** or **App Runner**
- [ ] Add an architecture diagram showing the AWS deployment

## Level 6 — Polish

- [ ] Add a screenshot and a short demo GIF to the README
- [ ] Add a `CONTRIBUTING.md`
- [ ] Tag a `v1.0.0` release

## Notes

- Nothing here requires paid services while learning: the simulator, SQLite and
  Streamlit all run free locally, and AWS has Always Free allowances for Lambda
  and DynamoDB at this scale.
- Keep commits small and descriptive — the history is part of the portfolio.
