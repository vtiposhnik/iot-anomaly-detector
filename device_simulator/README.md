# IoT Device Simulator

This simulator creates virtual IoT devices that send network traffic data to an MQTT broker, simulating real IoT devices in a network. It's designed to work with the IoT anomaly detection system by reading data from the IoT-23 dataset and publishing it to MQTT topics.

## Features

- Simulate multiple IoT devices sending network traffic data
- Support for different simulation modes:
  - Single device simulation
  - All devices simulation
  - Continuous random device simulation
  - Attack pattern simulation
- Configurable message intervals and counts
- Support for MQTT authentication
- Detailed logging

## Requirements

- Python 3.9-3.11 (recommended)
- MQTT broker (e.g., Mosquitto)
- IoT-23 dataset (processed by the anomaly detection system)

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Make sure you have an MQTT broker running (e.g., Mosquitto)

## Usage

### Basic Usage

Run the simulator in continuous mode (default):

```bash
python run_simulation.py
```

### Simulation Modes

#### Single Device Simulation

Simulate a specific device:

```bash
python run_simulation.py --mode single --device 1
```

#### All Devices Simulation

Simulate all devices in the dataset:

```bash
python run_simulation.py --mode all
```

#### Attack Pattern Simulation

Simulate an attack pattern:

```bash
python run_simulation.py --mode attack --duration 120
```

### Configuration Options

- `--broker`: MQTT broker hostname or IP (default: localhost)
- `--port`: MQTT broker port (default: 1883)
- `--username`: MQTT username (optional)
- `--password`: MQTT password (optional)
- `--qos`: MQTT Quality of Service level (default: 0)
- `--dataset`: Path to dataset CSV file
- `--interval`: Interval between messages in seconds (default: 1.0)
- `--count`: Number of records to send per device (default: 10)
- `--global-interval`: Interval between device simulations in seconds (default: 5.0)
- `--log-level`: Logging level (default: INFO)

## Environment Variables

You can also configure the simulator using environment variables or a `.env` file:

```
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=user
MQTT_PASSWORD=pass
MQTT_QOS=0
DATASET_PATH=../server2/data/processed/traffic.csv
DEFAULT_INTERVAL=1.0
DEFAULT_RECORDS_PER_DEVICE=10
GLOBAL_INTERVAL=5.0
LOG_LEVEL=INFO
```

## Integration with Anomaly Detection System

This simulator is designed to work with the IoT anomaly detection system. To use it:

1. Start the anomaly detection server:
   ```bash
   cd ../server2
   python app.py
   ```

2. Start the MQTT service in the anomaly detection server:
   ```bash
   curl -X POST http://localhost:5000/api/v1/mqtt/start
   ```

3. Run the device simulator:
   ```bash
   cd ../device_simulator
   python run_simulation.py
   ```

The simulator will send data to the MQTT broker, which will be processed by the anomaly detection system's MQTT adapter.
