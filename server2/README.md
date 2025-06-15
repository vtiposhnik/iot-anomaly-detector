# IoT Anomaly Detection System - FastAPI Backend

This is the Python-based backend implementation for the IoT monitoring application equipped with artificial intelligence to detect anomalies. The system is built with FastAPI for high performance and modern Python features.

## Architecture

The backend is developed entirely in Python and is responsible for:
- Traffic data ingestion
- Feature extraction
- Anomaly detection using machine learning models
- RESTful API endpoints for communication with the frontend

### FastAPI Framework

The system has been migrated from Flask to FastAPI, which offers several advantages:

- **Performance**: FastAPI is one of the fastest Python frameworks available, with performance on par with NodeJS and Go
- **Type Hints**: Built-in support for Python type hints, which improves code quality and IDE support
- **Automatic Documentation**: Interactive API documentation with Swagger UI and ReDoc
- **Data Validation**: Automatic request validation using Pydantic models
- **Modern Python**: Better support for modern Python features and async/await syntax

## Machine Learning Models

The system implements two anomaly detection models:

1. **Isolation Forest** - An ensemble-based method that explicitly isolates anomalies by randomly selecting a feature and then randomly selecting a split value between the maximum and minimum values of the selected feature.

2. **Local Outlier Factor (LOF)** - A density-based approach that computes the local density deviation of a given data point with respect to its neighbors. Anomalies are detected as points with substantially lower density than their neighbors.

## Generic Adapter System

The system now includes a flexible adapter system that can handle various types of network traffic data:

1. **CSV Adapter** - Handles CSV files with network traffic data, automatically mapping columns to our standard schema.

2. **JSON Adapter** - Processes JSON files, supporting both flat and nested structures with automatic field mapping.

3. **PCAP Adapter** - Parses packet capture files using Scapy, extracting network flows and relevant features.

4. **IoT-23 Adapter** - Specialized adapter for the IoT-23 dataset to maintain compatibility with our existing system.

This adapter system allows the anomaly detection pipeline to work with virtually any network traffic data source, making it truly "any-traffic" capable.

## Feature Extraction

The system extracts a comprehensive set of features from network traffic data:

- **Basic Features**: bytes_ratio, packet_rate, log-transformed metrics
- **Protocol Features**: One-hot encoded protocol information
- **Port Features**: Categorization of ports into well-known, registered, and dynamic ranges
- **Time-based Features**: Cyclical encoding of hour and day (when timestamp is available)
- **Service Features**: Categorization of common network services

## Usage

### Training Models

```bash
# Train models on CSV data
python train.py --input data/traffic.csv --output-dir models/

# Train models on PCAP data with custom contamination rate
python train.py --input data/capture.pcap --adapter pcap --contamination 0.05
```

### Detecting Anomalies

```bash
# Detect anomalies in new traffic data
python detect_anomalies.py --input data/new_traffic.csv

# Detect anomalies with custom threshold and save results
python detect_anomalies.py --input data/new_traffic.pcap --adapter pcap --threshold 0.8 --output results.csv --save-to-db
```

### API Usage

```bash
# Start the FastAPI server with Uvicorn
python run.py

# Or directly with Uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 5000

# Detect anomalies via API
curl -X POST http://localhost:5000/api/v1/detect \
  -H "Content-Type: application/json" \
  -d '{"device_id": 1, "threshold": 0.7, "model": "both"}'

# Check API status
curl http://localhost:5000/api/v1/status
```

### Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: Visit http://localhost:5000/docs for interactive documentation
- **ReDoc**: Visit http://localhost:5000/redoc for alternative documentation

These interfaces allow you to explore and test all API endpoints directly from your browser.

## Directory Structure

- `adapters/` - Data adapters for various input formats
  - `base_adapter.py` - Abstract base class for all adapters
  - `csv_adapter.py` - Adapter for CSV files
  - `json_adapter.py` - Adapter for JSON files
  - `pcap_adapter.py` - Adapter for PCAP files
  - `iot23_adapter.py` - Specialized adapter for IoT-23 dataset
  - `adapter_factory.py` - Factory for creating appropriate adapters

- `api/` - RESTful API endpoints
- `data/` - Data storage and processing
- `ml/` - Machine learning models and anomaly detection logic
- `models/` - Saved model files
- `utils/` - Utility functions for logging, data processing, etc.
- `app.py` - Main application entry point
- `initialize_models.py` - Script to initialize and train models

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Initialize and train the models:
   ```
   python initialize_models.py
   ```

3. Start the application:
   ```
   python app.py
   ```

## API Endpoints

- `GET /api/v1/status` - Get the status of the API and ML models
- `GET /api/v1/devices` - Get a list of all monitored devices
- `GET /api/v1/data` - Get sensor data (filterable by device and time range)
- `GET /api/v1/anomalies` - Get detected anomalies (filterable by device and time range)
- `POST /api/v1/detect` - Process new data and detect anomalies

## Data Format

The system expects IoT sensor data in the following format:

```json
{
  "id": "device1",
  "timestamp": "2023-03-01T08:00:00",
  "temperature": 65.2,
  "humidity": 42.3,
  "pressure": 1012.5,
  "vibration": 5.2,
  "network": {
    "packetLoss": 0.5,
    "latency": 25,
    "throughput": 950,
    "connectionCount": 12
  }
}
```

## Anomaly Detection

The system uses both Isolation Forest and Autoencoder models to detect anomalies. Anomalies are reported with:
- Device ID
- Timestamp
- Anomaly type
- Confidence score
- Affected features
- Description
