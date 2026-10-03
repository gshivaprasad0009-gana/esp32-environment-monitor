# Migrating this project to AWS

Level 5 of the [roadmap](../ROADMAP.md). This is a **plan**, not a description of
work already done — the migration has to be built in your own AWS account,
because it needs your credentials and it can incur charges if left running.

Read this alongside the AWS setup notes: create the account on the **Free plan**,
set a **billing alarm** first, and delete resources when you finish each step.

## Why do it

The pipeline already works. Moving it to AWS changes *where* each piece runs,
and in doing so touches five services that appear in almost every cloud job
description: IoT Core, Lambda, DynamoDB, IAM and EC2. The migration story —
"here is the on-premise version, here is the cloud version, here is what
changed and why" — is what makes the project interesting to an interviewer.

## What maps to what

| Today | On AWS | Why |
|---|---|---|
| Public MQTT broker | **AWS IoT Core** | Managed, authenticated MQTT with per-device certificates |
| `backend/ingest.py` | **Lambda** | Runs on each message; no server to keep alive |
| SQLite | **DynamoDB** | Serverless, Always Free at this scale |
| `backend/dashboard.py` | **EC2** or **App Runner** | Somewhere to host the Streamlit app |
| `backend/alerting.py` | **Lambda + SNS** | Alert on threshold breach, notify by email/SMS |
| `ml/train_model.py` | **Lambda** (scheduled) or SageMaker | Retrain periodically |

## Suggested order

Do these one at a time, and commit after each — each step is a working state.

### 1. AWS IoT Core instead of the public broker

- Create a *thing* for the ESP32 in IoT Core and download its certificates.
- Update the firmware to connect to your IoT Core endpoint with those
  certificates (the sketch's `MQTT_BROKER` becomes your account's endpoint, and
  it needs TLS + the device certificate).
- Confirm readings arrive in the IoT Core MQTT test client.

**Careful:** the device certificate is a credential. Keep it out of Git — it
belongs in `.gitignore` alongside `data/`.

### 2. Lambda instead of the ingest script

- Write a small handler that parses the incoming JSON and writes it to DynamoDB.
- Create the table with `device` as the partition key and a timestamp sort key.
- Give the Lambda an **IAM role** with write access to just that table —
  the principle of least privilege, and a talking point in interviews.

### 3. DynamoDB instead of SQLite

- The dashboard's `load_readings()` becomes a `boto3` query instead of a
  `sqlite3` call. Keep the DataFrame shape identical so the rest of the
  dashboard does not change.

### 4. Host the dashboard

- Simplest: an EC2 `t3.micro` running Streamlit behind a security group.
- Cleaner: containerise it and use App Runner.
- Either way, do not leave it running unattended — check the cost.

### 5. Alerts

- Move the threshold check into a Lambda triggered by the DynamoDB stream, and
  publish to an SNS topic with your email subscribed.

## What to write down as you go

- An architecture diagram of the AWS version (add it to `docs/`).
- The before/after: what got simpler, what got harder, what it costs.
- The parts you found confusing — those are the best answers to "what was the
  hardest thing you built?".

## Cost discipline

- Set a billing alarm on day one.
- Lambda and DynamoDB are Always Free at this volume.
- EC2 is the one to watch: stop the instance when you are not using it.
- Delete everything when you finish an experiment.
