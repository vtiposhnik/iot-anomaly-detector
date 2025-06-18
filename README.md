# IoT Anomaly Detection System

This repository contains an end‑to‑end platform for detecting anomalies in IoT network traffic.

- **server2/** – FastAPI backend providing data ingestion, machine learning utilities and MQTT services. See `server2/README.md` for detailed setup and API usage.
- **client/** – React frontend for visualising devices and anomalies. Usage instructions are in `client/README.md`.
- **device_simulator/** – Utility for publishing simulated IoT traffic over MQTT. See `device_simulator/README.md`.

Typical workflow:
1. Install backend dependencies and start the API (`python server2/run.py` or `uvicorn server2.main:app`).
2. Run the MQTT service and optionally the device simulator to generate traffic.
3. Open the web client to monitor incoming data and detected anomalies.

The backend stores data in a SQLite database and supports training and inference using Isolation Forest and LOF models. Dataset utilities for processing IoT‑23 data are located in `server2/utils` and `server2/ml`.

