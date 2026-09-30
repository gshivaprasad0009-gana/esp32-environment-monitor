# 🌡️ ESP32 Environment Monitor with ML Anomaly Detection

An end-to-end IoT project: an ESP32 with a DHT22 sensor streams live temperature and humidity over MQTT, a Python service stores the readings, a Streamlit dashboard visualises them in real time, and an Isolation Forest model flags unusual patterns — like a heat spike — before they become a problem.

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
├── data/                              # (generated) SQLite DB + trained model
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

## 🗺️ Roadmap

- [ ] Alert on anomaly (email / Telegram notification)
- [ ] Add more sensors (air quality, light)
- [ ] Deploy dashboard to the cloud
- [ ] Multiple ESP32 devices on one dashboard

## 🤝 Contributing

Suggestions welcome — open an issue or pull request.

## ✍️ Author

**Ganamolla Shiva Prasad** — B.Tech ECE student, building in Python, AI/ML, and embedded systems.
