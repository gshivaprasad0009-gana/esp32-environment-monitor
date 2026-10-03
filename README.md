# 🌡️ ESP32 Environment Monitor with ML Anomaly Detection

An end-to-end IoT project: an ESP32 with a DHT22 sensor streams live temperature and humidity over MQTT, a Python service stores the readings, a Streamlit dashboard visualises them in real time, and an Isolation Forest model flags unusual patterns — like a heat spike — before they become a problem.

## 🎯 The Problem It Solves

Monitoring a room, lab, or equipment rack usually means either checking a display by hand or buying a closed commercial system you cannot extend. This project builds the whole path yourself — sensor to dashboard to alert — so the data is yours and every layer can be changed. The anomaly detection matters because a slow drift or a sudden spike is easy to miss on a chart but obvious to a model watching the pattern.

```
[DHT22 sensor] → [ESP32] → WiFi → [MQTT broker] → [Python ingest] → [SQLite] → [Streamlit dashboard]
                                                                  ↘ [Isolation Forest ML] — anomaly flags
```

## ✨ Features

- 📡 **Real IoT pipeline** — sensor → firmware → MQTT → database → dashboard
- 🔌 **MQTT messaging** — the industry-standard IoT protocol
- 📊 **Live dashboard** — auto-refreshing charts of temperature & humidity
- 🤖 **ML anomaly detection** — Isolation Forest flags abnormal readings
- 🧪 **Works without hardware** — a simulator publishes the same messages as the real ESP32
- ✅ **Tested** — unit tests cover the pipeline logic, run automatically on every push

## 📁 Project structure

```
esp32-environment-monitor/
├── firmware/
│   ├── esp32_environment_monitor.ino   # ESP32 Arduino sketch (WiFi + DHT22 + MQTT)
│   └── README.md                       # wiring & library setup
├── simulator/
│   └── sensor_simulator.py            # fake ESP32 for testing without hardware
├── backend/
│   ├── ingest.py                      # MQTT subscriber → SQLite storage
│   └── dashboard.py                   # Streamlit live dashboard
├── ml/
│   └── train_model.py                 # trains the Isolation Forest anomaly detector
├── tests/
│   └── test_pipeline.py               # unit tests (no hardware or network needed)
├── .github/workflows/tests.yml        # runs the tests on every push
├── data/                              # (generated) SQLite DB + trained model
├── ROADMAP.md                         # planned improvements, in build order
├── LICENSE
└── requirements.txt
```

## 🚀 Quick start (no hardware needed)

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Start the ingest service** (terminal 1) — receives and stores readings

   ```bash
   python backend/ingest.py
   ```

3. **Start the sensor simulator** (terminal 2) — publishes readings like a real ESP32

   ```bash
   python simulator/sensor_simulator.py
   ```

4. **Train the anomaly detector** (terminal 3) — once you have some readings

   ```bash
   python ml/train_model.py
   ```

5. **Launch the dashboard**

   ```bash
   streamlit run backend/dashboard.py
   ```

   Open `http://localhost:8501` and watch the live data roll in. The simulator injects occasional temperature spikes — watch the ML model catch them in the anomaly panel.

## 🧪 Tests

The pipeline logic — the database layer, MQTT message handling, the simulator's output, and the anomaly detector — is covered by unit tests that need no hardware and no network connection:

```bash
pytest -q
```

These run automatically on every push via GitHub Actions (see `.github/workflows/tests.yml`).

## 🔩 Running on real hardware

See [`firmware/README.md`](firmware/README.md) for wiring, libraries, and setup. Once flashed, the ESP32 publishes to the same MQTT topic, so the rest of the pipeline works unchanged.

**Parts list (~₹600–850):**

| Component | Approx. price |
|---|---|
| ESP32 DevKit V1 | ₹300–500 |
| DHT22 temperature/humidity sensor | ₹200–350 |

## 🛠️ Technologies used

- **Firmware:** C++ (Arduino), PubSubClient, Adafruit DHT
- **Backend:** Python, paho-mqtt, SQLite
- **Dashboard:** Python, Streamlit, pandas
- **ML:** scikit-learn (Isolation Forest)
- **Testing:** pytest, GitHub Actions

## 🗺️ Roadmap

Planned improvements — small tweaks, extra sensors, alerts, real hardware, and an AWS migration — are tracked in [ROADMAP.md](ROADMAP.md), in the order they should be built.

## 🤝 Contributing

Suggestions welcome — open an issue or pull request.

## 📄 License

Released under the [MIT License](LICENSE).

## ✍️ Author

**Ganamolla Shiva Prasad** — B.Tech ECE student, building in Python, AI/ML, and embedded systems.
