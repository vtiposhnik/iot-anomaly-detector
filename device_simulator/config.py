"""
Configuration for the IoT Device Simulator

This module provides configuration settings for the IoT device simulator.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# MQTT Configuration
MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'localhost')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', 1883))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', None)
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', None)
MQTT_QOS = int(os.getenv('MQTT_QOS', 0))

# Dataset Configuration
BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = os.getenv(
    'DATASET_PATH',
    str((BASE_DIR.parent / 'server2' / 'data' / 'processed' / 'traffic.csv').resolve())
)

# Simulation Configuration
DEFAULT_INTERVAL = float(os.getenv('DEFAULT_INTERVAL', 1.0))
DEFAULT_RECORDS_PER_DEVICE = int(os.getenv('DEFAULT_RECORDS_PER_DEVICE', 10))
GLOBAL_INTERVAL = float(os.getenv('GLOBAL_INTERVAL', 5.0))

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
