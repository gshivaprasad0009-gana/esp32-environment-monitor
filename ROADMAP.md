# Roadmap

Where this project is going, in the order it was built. Each level is a working
milestone.

## ✅ Level 1 — Small tweaks *(done)*

- [x] Make the publish interval configurable (`PUBLISH_INTERVAL_SECONDS`)
- [x] Add a Celsius / Fahrenheit toggle to the dashboard
- [x] Make the anomaly sensitivity adjustable from the dashboard

## ✅ Level 2 — More sensors *(done)*

- [x] Add a light sensor (LDR) to the firmware, simulator, database and dashboard
- [x] Show light as its own metric and chart
- [x] Include light in the anomaly detection features

## ✅ Level 3 — Alerts *(done)*

- [x] Alert when a reading breaches a temperature threshold (`ALERT_TEMP_THRESHOLD`)
- [x] Optional Telegram notifications (console fallback with no configuration)
- [x] A "recent alerts" panel on the dashboard

## ⏳ Level 4 — Real hardware *(needs parts)*

Cannot be done in software — this needs the physical components.

- [ ] Order an ESP32 DevKit V1, a DHT22 module and an LDR
- [ ] Flash the firmware and confirm real readings reach the dashboard
- [ ] Document the wiring with photos

The firmware already supports all three sensors, so once the parts arrive this
is a flashing exercise rather than a coding one. See `firmware/README.md`.

## ⏳ Level 5 — Migrate to AWS *(needs an AWS account)*

The flagship step. It cannot be completed from here because it requires an AWS
account with billing and credentials — it should be built by you, in your own
account, following `docs/aws-migration.md`.

- [ ] Replace the public MQTT broker with **AWS IoT Core**
- [ ] Replace the ingest script with a **Lambda** function
- [ ] Replace SQLite with **DynamoDB**
- [ ] Host the dashboard on **EC2** or **App Runner**
- [ ] Add an architecture diagram showing the AWS deployment

## ✅ Level 6 — Polish *(done, except the app screenshot)*

- [x] Add an architecture diagram (`docs/architecture.png`)
- [x] Add a sample-output chart (`docs/sample-output.png`)
- [x] Add a `CONTRIBUTING.md`
- [ ] Add a screenshot of the running dashboard — this has to be captured from
      a machine where the app is running (`streamlit run backend/dashboard.py`,
      then screenshot the browser). It could not be captured automatically here.
- [ ] Tag a `v1.0.0` release

## Notes

- Nothing here requires paid services while learning: the simulator, SQLite and
  Streamlit all run free locally, and AWS has Always Free allowances for Lambda
  and DynamoDB at this scale.
- Keep commits small and descriptive — the history is part of the portfolio.
