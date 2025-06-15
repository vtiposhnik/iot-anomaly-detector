"""
IoT Device Simulator

This module provides a simulator for IoT devices that sends network traffic data
to an MQTT broker, simulating real IoT devices in a network.
"""
import paho.mqtt.client as mqtt
import pandas as pd
import json
import time
import random
import logging
from datetime import datetime
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from device_simulator.config import (
    MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_USERNAME, 
    MQTT_PASSWORD, MQTT_QOS, DATASET_PATH,
    DEFAULT_INTERVAL, DEFAULT_RECORDS_PER_DEVICE, GLOBAL_INTERVAL,
    LOG_LEVEL
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('IoTDeviceSimulator')

class IoTDeviceSimulator:
    """
    Simulator for IoT devices that sends network traffic data to an MQTT broker.
    
    This class reads data from the IoT-23 dataset and sends it to an MQTT broker,
    simulating real IoT devices in a network.
    """
    
    def __init__(self, broker_host=MQTT_BROKER_HOST, broker_port=MQTT_BROKER_PORT, 
                 username=MQTT_USERNAME, password=MQTT_PASSWORD, qos=MQTT_QOS,
                 dataset_path=DATASET_PATH):
        """
        Initialize the IoT device simulator
        
        Args:
            broker_host: MQTT broker hostname or IP
            broker_port: MQTT broker port
            username: MQTT username (optional)
            password: MQTT password (optional)
            qos: Quality of Service level
            dataset_path: Path to the dataset CSV file
        """
        # MQTT client setup
        self.client_id = f"iot_device_sim_{random.randint(1000, 9999)}"
        self.client = mqtt.Client(client_id=self.client_id)
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.qos = qos
        
        # Load dataset
        try:
            self.dataset = pd.read_csv(dataset_path)
            self.device_groups = self.dataset.groupby('device_id')
            self.devices = list(self.device_groups.groups.keys())
            
            logger.info(f"Loaded {len(self.dataset)} records for {len(self.devices)} devices from {dataset_path}")
        except Exception as e:
            logger.error(f"Error loading dataset from {dataset_path}: {str(e)}")
            raise
    
    def connect(self):
        """
        Connect to the MQTT broker
        
        Returns:
            Boolean indicating success
        """
        try:
            # Set username and password if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Connect to broker
            self.client.connect(self.broker_host, self.broker_port)
            
            # Start the loop
            self.client.loop_start()
            
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            return True
        
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {str(e)}")
            return False
    
    def disconnect(self):
        """
        Disconnect from the MQTT broker
        
        Returns:
            Boolean indicating success
        """
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")
            return True
        
        except Exception as e:
            logger.error(f"Error disconnecting from MQTT broker: {str(e)}")
            return False
    
    def simulate_device(self, device_id, interval=DEFAULT_INTERVAL, count=None):
        """
        Simulate a specific device sending data
        
        Args:
            device_id: ID of the device to simulate
            interval: Interval between messages (seconds)
            count: Number of records to send (None for all)
            
        Returns:
            Number of records sent
        """
        if device_id not in self.devices:
            logger.warning(f"Device {device_id} not found in dataset")
            return 0
        
        device_data = self.device_groups.get_group(device_id)
        records_sent = 0
        
        for _, row in device_data.iterrows():
            if count is not None and records_sent >= count:
                break
                
            # Prepare message payload
            payload = {
                'timestamp': datetime.now().isoformat(),
                'device_id': int(device_id),
                'src_ip': row['source_ip'],
                'dst_ip': row['dest_ip'],
                'src_port': int(row['source_port']),
                'dst_port': int(row['dest_port']),
                'protocol': row['protocol'],
                'duration': float(row['duration']),
                'orig_bytes': int(row['orig_bytes']),
                'resp_bytes': int(row['resp_bytes']),
                'packet_size': int(row['packet_size'])
            }
            
            # Add optional fields if present
            for field in ['service', 'conn_state', 'label', 'attack_type']:
                if field in row and not pd.isna(row[field]):
                    payload[field] = row[field]
            
            # Send to MQTT topic
            topic = f"iot/{device_id}/data"
            self.client.publish(topic, json.dumps(payload), qos=self.qos)
            logger.debug(f"Sent data for device {device_id} to topic {topic}")
            
            records_sent += 1
            time.sleep(interval)  # Wait between messages
        
        logger.info(f"Sent {records_sent} records for device {device_id}")
        return records_sent
    
    def simulate_all_devices(self, interval=DEFAULT_INTERVAL, records_per_device=DEFAULT_RECORDS_PER_DEVICE):
        """
        Simulate all devices sending data
        
        Args:
            interval: Interval between messages (seconds)
            records_per_device: Number of records to send per device
            
        Returns:
            Dictionary with device IDs and number of records sent
        """
        results = {}
        
        for device_id in self.devices:
            logger.info(f"Simulating device {device_id}")
            records_sent = self.simulate_device(device_id, interval, records_per_device)
            results[device_id] = records_sent
        
        return results
    
    def run_continuous_simulation(self, global_interval=GLOBAL_INTERVAL):
        """
        Run a continuous simulation with random device selection
        
        Args:
            global_interval: Interval between device simulations (seconds)
            
        Returns:
            None
        """
        try:
            logger.info("Starting continuous simulation. Press Ctrl+C to stop.")
            
            while True:
                # Pick a random device
                device_id = random.choice(self.devices)
                
                # Send a few records
                records_to_send = random.randint(3, 8)
                logger.info(f"Simulating device {device_id} with {records_to_send} records")
                self.simulate_device(device_id, interval=0.5, count=records_to_send)
                
                # Wait before next device
                time.sleep(global_interval)
        
        except KeyboardInterrupt:
            logger.info("Simulation stopped by user")
        
        finally:
            # Disconnect from broker
            self.disconnect()
    
    def simulate_attack_pattern(self, attack_type=None, duration=60):
        """
        Simulate a specific attack pattern
        
        Args:
            attack_type: Type of attack to simulate (None for random)
            duration: Duration of the attack simulation (seconds)
            
        Returns:
            Number of records sent
        """
        # Filter dataset for attack records
        attack_data = self.dataset[self.dataset['label'] == 'malicious']
        
        if attack_type:
            attack_data = attack_data[attack_data['attack_type'] == attack_type]
        
        if attack_data.empty:
            logger.warning(f"No {'attack' if not attack_type else attack_type} data found in dataset")
            return 0
        
        # Group by device
        attack_devices = attack_data['device_id'].unique()
        
        if not len(attack_devices):
            logger.warning("No devices found with attack data")
            return 0
        
        logger.info(f"Simulating attack pattern for {len(attack_devices)} devices over {duration} seconds")
        
        # Calculate timing
        start_time = time.time()
        end_time = start_time + duration
        records_sent = 0
        
        try:
            while time.time() < end_time:
                # Pick a random device with attack data
                device_id = random.choice(attack_devices)
                
                # Get attack data for this device
                device_attack_data = attack_data[attack_data['device_id'] == device_id]
                
                # Send a random attack record
                row = device_attack_data.sample(1).iloc[0]
                
                # Prepare message payload
                payload = {
                    'timestamp': datetime.now().isoformat(),
                    'device_id': int(device_id),
                    'src_ip': row['source_ip'],
                    'dst_ip': row['dest_ip'],
                    'src_port': int(row['source_port']),
                    'dst_port': int(row['dest_port']),
                    'protocol': row['protocol'],
                    'duration': float(row['duration']),
                    'orig_bytes': int(row['orig_bytes']),
                    'resp_bytes': int(row['resp_bytes']),
                    'packet_size': int(row['packet_size']),
                    'label': 'malicious',
                    'attack_type': row['attack_type'] if 'attack_type' in row else 'unknown'
                }
                
                # Send to MQTT topic
                topic = f"iot/{device_id}/data"
                self.client.publish(topic, json.dumps(payload), qos=self.qos)
                
                records_sent += 1
                
                # Wait a short time between messages
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            logger.info("Attack simulation stopped by user")
        
        logger.info(f"Sent {records_sent} attack records")
        return records_sent

# For testing
if __name__ == "__main__":
    # Create simulator
    simulator = IoTDeviceSimulator()
    
    # Connect to broker
    if simulator.connect():
        # Run simulation
        simulator.run_continuous_simulation()
    else:
        logger.error("Failed to connect to MQTT broker")
