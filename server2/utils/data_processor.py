"""
Data processing utilities for the IoT Anomaly Detection System
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.logger import get_logger

# Get logger
logger = get_logger()

def load_csv_data(file_path):
    """
    Load data from a CSV file
    
    Args:
        file_path: Path to the CSV file
    
    Returns:
        DataFrame containing the data
    """
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} records from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading data from {file_path}: {str(e)}")
        return pd.DataFrame()

def prepare_training_data(source_path=None, target_path=None):
    """
    Prepare training data for anomaly detection models
    
    Args:
        source_path: Path to the source data file
        target_path: Path to save the processed training data
    
    Returns:
        DataFrame containing the processed training data
    """
    # Default paths
    if source_path is None:
        source_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'public', 'data', 'iot_sensor_data.csv'
        )
    
    if target_path is None:
        target_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data', 'training_data.csv'
        )
    
    try:
        # Load data
        df = load_csv_data(source_path)
        
        if df.empty:
            logger.error("No data loaded for training")
            return df
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Save processed data
        df.to_csv(target_path, index=False)
        logger.info(f"Saved {len(df)} records to {target_path}")
        
        return df
    
    except Exception as e:
        logger.error(f"Error preparing training data: {str(e)}")
        return pd.DataFrame()

def generate_synthetic_data(num_devices=3, num_days=7, interval_minutes=15, anomaly_rate=0.05):
    """
    Generate synthetic IoT sensor data for testing
    
    Args:
        num_devices: Number of devices to simulate
        num_days: Number of days of data to generate
        interval_minutes: Interval between readings in minutes
        anomaly_rate: Percentage of readings that should be anomalous
    
    Returns:
        DataFrame containing synthetic data
    """
    try:
        # Calculate number of readings per device
        readings_per_day = 24 * 60 // interval_minutes
        total_readings = num_days * readings_per_day
        
        # Initialize data storage
        data = []
        
        # Generate timestamps
        end_time = datetime.now()
        start_time = end_time - timedelta(days=num_days)
        timestamps = [
            start_time + timedelta(minutes=i*interval_minutes)
            for i in range(total_readings)
        ]
        
        # Normal ranges for each sensor type
        normal_ranges = {
            'temperature': (60, 75),
            'humidity': (40, 50),
            'pressure': (1010, 1015),
            'vibration': (4, 7)
        }
        
        # Anomaly ranges for each sensor type
        anomaly_ranges = {
            'temperature': [(30, 50), (85, 100)],
            'humidity': [(10, 30), (70, 90)],
            'pressure': [(980, 1000), (1025, 1040)],
            'vibration': [(0, 2), (15, 25)]
        }
        
        # Generate data for each device
        for device_id in range(1, num_devices + 1):
            device_name = f"device{device_id}"
            
            # Generate readings for this device
            for timestamp in timestamps:
                # Determine if this reading should be anomalous
                is_anomaly = np.random.random() < anomaly_rate
                status = 'normal'
                
                # Generate sensor values
                if is_anomaly:
                    # Choose which sensor will be anomalous
                    anomalous_sensor = np.random.choice(list(normal_ranges.keys()))
                    
                    # Generate values
                    temperature = np.random.uniform(*normal_ranges['temperature'])
                    humidity = np.random.uniform(*normal_ranges['humidity'])
                    pressure = np.random.uniform(*normal_ranges['pressure'])
                    vibration = np.random.uniform(*normal_ranges['vibration'])
                    
                    # Make the chosen sensor anomalous
                    anomaly_range = np.random.choice(anomaly_ranges[anomalous_sensor])
                    if anomalous_sensor == 'temperature':
                        temperature = np.random.uniform(*anomaly_range)
                        status = 'warning' if temperature < 85 else 'critical'
                    elif anomalous_sensor == 'humidity':
                        humidity = np.random.uniform(*anomaly_range)
                        status = 'warning' if humidity < 70 else 'critical'
                    elif anomalous_sensor == 'pressure':
                        pressure = np.random.uniform(*anomaly_range)
                        status = 'warning'
                    elif anomalous_sensor == 'vibration':
                        vibration = np.random.uniform(*anomaly_range)
                        status = 'warning' if vibration < 15 else 'critical'
                else:
                    # Generate normal values with some random variation
                    temperature = np.random.uniform(*normal_ranges['temperature'])
                    humidity = np.random.uniform(*normal_ranges['humidity'])
                    pressure = np.random.uniform(*normal_ranges['pressure'])
                    vibration = np.random.uniform(*normal_ranges['vibration'])
                
                # Add reading to data
                data.append({
                    'id': device_name,
                    'timestamp': timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
                    'temperature': round(temperature, 1),
                    'humidity': round(humidity, 1),
                    'pressure': round(pressure, 1),
                    'vibration': round(vibration, 1),
                    'status': status
                })
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        logger.info(f"Generated {len(df)} synthetic readings for {num_devices} devices")
        return df
    
    except Exception as e:
        logger.error(f"Error generating synthetic data: {str(e)}")
        return pd.DataFrame()

def save_to_csv(df, file_path):
    """
    Save DataFrame to CSV file
    
    Args:
        df: DataFrame to save
        file_path: Path to save the CSV file
    
    Returns:
        Boolean indicating success
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save to CSV
        df.to_csv(file_path, index=False)
        logger.info(f"Saved {len(df)} records to {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving data to {file_path}: {str(e)}")
        return False
