# Contributing

Thanks for taking a look at this project. It is primarily a learning project,
so contributions that improve clarity, correctness, or documentation are all
welcome.

## Getting set up

```bash
git clone https://github.com/gshivaprasad0009-gana/esp32-environment-monitor.git
cd esp32-environment-monitor
pip install -r requirements.txt
```

## Before you open a pull request

1. **Run the tests.** They must pass:

   ```bash
   pytest -q
   ```

2. **Run the pipeline once** to make sure your change works end to end:

   ```bash
   python backend/ingest.py            # terminal 1
   python simulator/sensor_simulator.py  # terminal 2
   python ml/train_model.py            # terminal 3, after a minute
   streamlit run backend/dashboard.py  # terminal 4
   ```

3. **Keep commits small and descriptive.** A commit like
   `feat: add light sensor to the pipeline` is far more useful than
   `updates`.

## Code style

- Python: follow [PEP 8](https://peps.python.org/pep-0008/). Keep functions
  short and give them clear names.
- Comment the *why*, not the *what* — the code already says what it does.
- New behaviour needs a test in `tests/test_pipeline.py`.

## Configuration

Settings are read from environment variables with sensible defaults, so the
project runs with no setup. **Never commit secrets** (tokens, passwords, API
keys) — use environment variables, and see `backend/alerting.py` for the
pattern.

## Reporting a problem

Open an issue and include:

- what you expected to happen
- what actually happened
- the exact command you ran and any error text

## Areas that would help most

See [ROADMAP.md](ROADMAP.md) for the planned work. The most useful next steps
are the AWS migration (Level 5) and adding screenshots (Level 6).
