# 📖 Project Guide — ESP32 Environment Monitor

Everything about this project, explained from the ground up. Written for
someone learning, so it assumes no prior knowledge.

**Repository:** `esp32-environment-monitor`
**What it is in one line:** a complete IoT system that reads a room's
temperature, humidity and light, sends the readings over the internet, stores
them, shows them on a live dashboard, and raises an alert when something looks
wrong.

---

## 1. What problem does it solve?

Imagine you want to know whether a lab, a server rack, or a greenhouse is
getting too hot. Your options are usually:

- **Walk over and look at a display.** Fine until you forget, or until it
  happens at 3am.
- **Buy a commercial monitoring box.** It works, but it is closed — you cannot
  change what it measures, where the data goes, or what it alerts on.

This project builds the whole path yourself, so every layer is yours to change.
It is also, deliberately, a *complete* example: sensor → firmware → network →
storage → visualisation → alerting. Most student projects do one or two of
those. Doing all of them is what makes it a systems project.

---

## 2. The big picture

```
   ┌──────────────┐
   │ DHT22 sensor │  measures temperature + humidity
   │ LDR sensor   │  measures light
   └──────┬───────┘
          │ wires
   ┌──────▼───────┐
   │    ESP32     │  a small computer — reads the sensors
   └──────┬───────┘
          │ WiFi
   ┌──────▼───────┐
   │ MQTT broker  │  a message postbox on the internet
   └──────┬───────┘
          │ subscribe
   ┌──────▼───────┐
   │  ingest.py   │  receives each reading
   └──────┬───────┘
          │ writes
   ┌──────▼───────┐
   │   SQLite     │  a database file on disk
   └──┬────────┬──┘
      │        │
      │        └──────────────► train_model.py ──► anomaly scores
      │
      └──► dashboard.py (live charts)      alerting.py (raises alerts)
```

The key idea: **each box does one job and does not know about the others.**
The sensor does not know a dashboard exists. The dashboard does not know where
the data came from. That separation is why you can replace any one piece
without touching the rest — for example, swapping the public broker for AWS
IoT Core later.

---

## 3. Every technology used, and what it is

| Technology | What it actually is | Where it appears |
|---|---|---|
| **ESP32** | A small, cheap microcontroller with built-in WiFi. It is a tiny computer that runs one program forever and has pins you can attach sensors to. | `firmware/` |
| **DHT22** | A digital sensor that measures temperature and humidity. | `firmware/` |
| **LDR** | A light-dependent resistor — its resistance changes with light. Read through an analog pin. | `firmware/` |
| **Arduino / C++** | The language and tooling the ESP32 runs. Not Python — microcontrollers are too small for it. | `firmware/*.ino` |
| **MQTT** | A lightweight messaging protocol built for sensors. Instead of asking "give me data", a *publisher* sends messages to a *topic*, and anyone *subscribed* to that topic receives them. The postbox analogy is exact. | firmware, simulator, ingest |
| **paho-mqtt** | The Python library that speaks MQTT. | `simulator/`, `backend/ingest.py` |
| **JSON** | A simple text format for structured data: `{"temperature": 27.5}`. Every layer speaks it. | everywhere |
| **SQLite** | A database that lives in a single file. No server to install. Perfect for learning and for small projects. | `backend/ingest.py` |
| **Python** | The language of the backend, the dashboard and the ML. | most files |
| **Streamlit** | A Python library that turns a script into a web page. You write Python; it draws the browser UI. No HTML or JavaScript needed. | `backend/dashboard.py` |
| **pandas** | Python's table library. Used to read the database into a table and hand it to Streamlit for charting. | `backend/dashboard.py` |
| **scikit-learn** | The standard Python machine-learning library. Here it provides **Isolation Forest**. | `ml/train_model.py` |
| **Isolation Forest** | An algorithm that finds odd rows in a table. The intuition: if you repeatedly split the data at random, unusual points get separated in fewer splits — so "how quickly did this point get isolated?" is an anomaly score. | `ml/train_model.py` |
| **Environment variables** | Settings passed in from outside the program (`PUBLISH_INTERVAL_SECONDS=30`), so you do not edit code to change behaviour, and secrets never live in files. | all scripts |
| **pytest** | The Python testing tool. | `tests/` |
| **GitHub Actions** | A service that runs your tests automatically every time you push code. | `.github/workflows/tests.yml` |
| **Telegram Bot API** | An optional way to send yourself a phone notification when an alert fires. | `backend/alerting.py` |

---

## 4. File-by-file: what each one does

### `firmware/esp32_environment_monitor.ino`
The program on the physical board. It connects to WiFi, connects to the MQTT
broker, then every 5 seconds reads the DHT22 (temperature, humidity) and the LDR
(light), builds a JSON message, and publishes it to the topic
`esp32/env-monitor/data`.

Key detail: the LDR is read on **GPIO 34**, which is an *input-only analog pin* —
a detail that matters because not every pin can read an analog voltage.

### `firmware/README.md`
The wiring diagram, the libraries to install in the Arduino IDE, and the parts
list with prices. Read this before buying anything.

### `simulator/sensor_simulator.py`
**The most useful file in the project.** It pretends to be an ESP32: it
generates believable readings and publishes them in exactly the same format.
Because of this, the entire pipeline can be built and tested with **no
hardware at all**. It also injects occasional temperature spikes so the anomaly
detector has something to find.

### `backend/ingest.py`
Subscribes to the MQTT topic. Every time a message arrives it parses the JSON
and inserts a row into the database. It also creates the table on first run,
and *migrates* an older database by adding the `light` column if it is missing —
so upgrading does not mean throwing away your data.

### `backend/alerting.py`
Watches for readings above a temperature threshold. When one appears it records
it in an `alerts` table (so the dashboard can show history) and sends a
notification — Telegram if configured, otherwise prints to the console.

Notice the design: with no configuration at all it still works. That is what
makes a project usable by someone else.

### `backend/dashboard.py`
The web page. It reads the database, draws charts, and adds a few controls:
a °C/°F toggle and an anomaly-sensitivity slider. The slider works by taking a
*percentile* of the model's scores, so changing it re-flags readings instantly
without retraining anything.

### `ml/train_model.py`
Trains the Isolation Forest on the stored readings and saves it to a file.
If there is not enough real data yet it falls back to a deterministic synthetic
seed set — so the dashboard works on day one.

### `tests/test_pipeline.py`
19 tests. They check the database layer and its migration, how malformed MQTT
messages are handled, the simulator's output and its configuration, the model's
ability to flag a spike, the dashboard's logic, and the alerting rules. **All of
this runs without hardware and without a network connection** — which is what
makes it a real test suite rather than a demo.

### The other files
- `README.md` — the front page: features, quick start, configuration, hardware
- `ROADMAP.md` — what is done and what comes next, level by level
- `CONTRIBUTING.md` — how someone else would contribute
- `LICENSE` — MIT: anyone may use, modify and share this code
- `docs/architecture.png` — the diagram above, as an image
- `docs/sample-output.png` — real readings plotted from the database
- `docs/aws-migration.md` — the plan for moving this onto AWS

---

## 5. How to run it

```bash
pip install -r requirements.txt

python backend/ingest.py              # terminal 1 — receives readings
python simulator/sensor_simulator.py  # terminal 2 — produces readings
python ml/train_model.py              # terminal 3 — after a few minutes
python backend/alerting.py            # terminal 4 — optional
streamlit run backend/dashboard.py    # terminal 5 — the web page
```

Then open `http://localhost:8501`.

**What "working" looks like:** charts filling with data within seconds, and
every so often a spike appearing — with the dashboard's anomaly panel catching it.

---

## 6. Concepts worth understanding (in this order)

1. **A dictionary in Python** — because that is what the JSON message becomes
2. **A `for` loop** — the simulator's main loop
3. **What a function is** — `make_reading()` in the simulator is a good first one
4. **A database table** — rows and columns, like a spreadsheet
5. **Publish / subscribe** — the MQTT idea
6. **What a test is** — a function that asserts something is true

You do not need to understand Isolation Forest to run this project. You do need
to understand items 1–3 to read any of it.

---

## 7. Common problems and what they mean

| Symptom | What is happening | Fix |
|---|---|---|
| `python: command not found` | Python is not installed, or not on your PATH | Reinstall Python and tick **"Add Python to PATH"** |
| `ModuleNotFoundError: No module named 'paho'` | Dependencies not installed | Run `pip install -r requirements.txt` |
| `Connection refused` / broker errors | Port 1883 is blocked (common on college WiFi) | Try a home network or a mobile hotspot |
| Dashboard shows "No readings yet" | The ingest service is not running, or has just started | Start `ingest.py` first, then the simulator |
| Nothing appears in the charts | The dashboard was opened before any data arrived | Wait a few seconds — it refreshes itself |

---

## 8. What you would say about this project in an interview

> "It's an end-to-end IoT pipeline. An ESP32 reads three sensors and publishes
> over MQTT. A Python service stores the readings in SQLite, a Streamlit
> dashboard shows them live, and an Isolation Forest flags unusual readings.
> The parts I'd highlight: it runs without hardware because there's a simulator
> that publishes the identical message format; the tests need no network; and
> there's a written plan for migrating it to AWS IoT Core and DynamoDB."

That last sentence is the one that makes an interviewer lean forward — it shows
you understand the system well enough to know where it goes next.

---

## 9. Where this project goes next

See [`../ROADMAP.md`](../ROADMAP.md). In short: real hardware, then the AWS
migration in [`aws-migration.md`](aws-migration.md), then perhaps running the
neural network from the `neurosense` project directly on the ESP32.
