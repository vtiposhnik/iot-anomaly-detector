"""
IoT-23 Dataset Processor for IoT Anomaly Detection System

This script downloads and processes a subset of the IoT-23 dataset,
transforming it to match our database schema.
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime
from utils.logger import get_logger

# Get logger
logger = get_logger()

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DATASET_DIR = os.path.join(DATA_DIR, 'iot23')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')

# Ensure directories exist
os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def process_iot23_dataset(file_path=None):
    """
    Process the IoT-23 dataset to match our database schema
    
    Args:
        file_path: Path to the dataset file
    
    Returns:
        Dictionary containing processed dataframes
    """
    if file_path is None:
        file_path = os.path.join(DATASET_DIR, 'conn.log.labeled')
    
    if not os.path.exists(file_path):
        logger.error(f"Dataset file not found: {file_path}")
        return None
    
    try:
        logger.info(f"Processing dataset: {file_path}")
        
        # Read the dataset
        # IoT-23 conn.log.labeled has a custom format, we need to parse it
        # This is a simplified parser for demonstration
        data = []
        with open(file_path, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                
                # Parse the line
                fields = line.strip().split('\t')
                if len(fields) < 20:
                    continue
                
                try:
                    # Extract relevant fields
                    timestamp = fields[0]
                    uid = fields[1]
                    source_ip = fields[2]
                    source_port = fields[3]
                    dest_ip = fields[4]
                    dest_port = fields[5]
                    protocol = fields[6]
                    service = fields[7]
                    duration = fields[8]
                    orig_bytes = fields[9]
                    resp_bytes = fields[10]
                    conn_state = fields[11]
                    
                    # The last two fields contain the label and attack type
                    if len(fields) >= 22:
                        label = fields[-2]  # Second to last field is the label (Malicious/Benign)
                        attack_type = fields[-1]  # Last field is the attack type
                    else:
                        label = 'Unknown'
                        attack_type = '-'
                    
                    # Convert to appropriate types
                    try:
                        orig_bytes = int(orig_bytes) if orig_bytes != '-' else 0
                        resp_bytes = int(resp_bytes) if resp_bytes != '-' else 0
                        duration = float(duration) if duration != '-' else 0.0
                    except:
                        orig_bytes = 0
                        resp_bytes = 0
                        duration = 0.0
                    
                    # Add to data
                    data.append({
                        'timestamp': timestamp,
                        'uid': uid,
                        'source_ip': source_ip,
                        'source_port': source_port,
                        'dest_ip': dest_ip,
                        'dest_port': dest_port,
                        'protocol': protocol,
                        'service': service,
                        'duration': duration,
                        'orig_bytes': orig_bytes,
                        'resp_bytes': resp_bytes,
                        'conn_state': conn_state,
                        'label': label,
                        'attack_type': attack_type
                    })
                except Exception as e:
                    logger.warning(f"Error parsing line: {str(e)}")
                    continue
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Process the data to match our schema
        
        # 1. Extract devices (db_device)
        devices = set(df['source_ip'].unique()) | set(df['dest_ip'].unique())
        device_df = pd.DataFrame({
            'device_id': range(1, len(devices) + 1),
            'ip_address': list(devices),
            'type_id': 1,  # Default type
            'status': True,
            'last_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Create a mapping of IP to device_id
        ip_to_device_id = dict(zip(device_df['ip_address'], device_df['device_id']))
        
        # 2. Create traffic data (db_traffic_devices)
        traffic_df = df.copy()
        traffic_df['log_id'] = range(1, len(traffic_df) + 1)
        traffic_df['link_id'] = 1  # Default link
        traffic_df['device_id'] = traffic_df['source_ip'].map(ip_to_device_id)
        traffic_df['packet_size'] = traffic_df['orig_bytes'] + traffic_df['resp_bytes']
        
        # 3. Create links (db_link)
        links = []
        for _, row in traffic_df.iterrows():
            source_id = ip_to_device_id.get(row['source_ip'], 0)
            dest_id = ip_to_device_id.get(row['dest_ip'], 0)
            
            if source_id > 0 and dest_id > 0:
                links.append((source_id, dest_id))
        
        unique_links = list(set(links))
        link_df = pd.DataFrame({
            'id': range(1, len(unique_links) + 1),
            'abonent_id': [link[0] for link in unique_links],
            'address_id': [link[1] for link in unique_links]
        })
        
        # 4. Create anomalies (db_device_anomalies)
        # Print sample data for debugging
        print("\nSample labels from dataset:")
        print(df['label'].value_counts())
        
        if 'attack_type' in df.columns:
            print("\nSample attack types:")
            print(df['attack_type'].value_counts())
        
        # Check for malicious entries
        anomaly_df = traffic_df[traffic_df['label'] == 'Malicious'].copy()
        print(f"\nFound {len(anomaly_df)} malicious entries")
        
        anomaly_df['anomaly_id'] = range(1, len(anomaly_df) + 1) if len(anomaly_df) > 0 else []
        anomaly_df['type_id'] = 1  # Default type
        anomaly_df['score'] = 0.9  # High confidence for labeled anomalies
        anomaly_df['is_genuine'] = True
        anomaly_df['model_used'] = 'IoT-23 Labels'
        anomaly_df['detected_at'] = anomaly_df['timestamp']
        
        # Save processed data
        device_df.to_csv(os.path.join(PROCESSED_DIR, 'devices.csv'), index=False)
        traffic_df.to_csv(os.path.join(PROCESSED_DIR, 'traffic.csv'), index=False)
        link_df.to_csv(os.path.join(PROCESSED_DIR, 'links.csv'), index=False)
        anomaly_df.to_csv(os.path.join(PROCESSED_DIR, 'anomalies.csv'), index=False)
        
        logger.info(f"Dataset processed successfully")
        logger.info(f"Devices: {len(device_df)}")
        logger.info(f"Traffic records: {len(traffic_df)}")
        logger.info(f"Links: {len(link_df)}")
        logger.info(f"Anomalies: {len(anomaly_df)}")
        
        return {
            'devices': device_df,
            'traffic': traffic_df,
            'links': link_df,
            'anomalies': anomaly_df
        }
    
    except Exception as e:
        logger.error(f"Error processing dataset: {str(e)}")
        return None

def create_training_data():
    """
    Create training data for our ML models from the processed dataset
    
    Returns:
        Path to the training data file
    """
    try:
        # Load processed traffic data
        traffic_path = os.path.join(PROCESSED_DIR, 'traffic.csv')
        anomalies_path = os.path.join(PROCESSED_DIR, 'anomalies.csv')
        
        if not os.path.exists(traffic_path) or not os.path.exists(anomalies_path):
            logger.error("Processed data not found. Run process_iot23_dataset first.")
            return None
        
        traffic_df = pd.read_csv(traffic_path)
        anomalies_df = pd.read_csv(anomalies_path)
        
        # Create a set of anomalous log_ids
        anomalous_logs = set(anomalies_df['log_id'])
        
        # Add a label column to the traffic data
        traffic_df['is_anomaly'] = traffic_df['log_id'].apply(lambda x: x in anomalous_logs)
        
        # Extract features for training
        features = [
            'device_id', 'packet_size', 'duration', 'orig_bytes', 'resp_bytes'
        ]
        
        # Create training data
        training_df = traffic_df[features + ['is_anomaly']].copy()
        
        # Save training data
        training_path = os.path.join(DATA_DIR, 'training_data.csv')
        training_df.to_csv(training_path, index=False)
        
        logger.info(f"Training data created: {training_path}")
        logger.info(f"Total records: {len(training_df)}")
        logger.info(f"Anomalies: {training_df['is_anomaly'].sum()}")
        
        return training_path
    
    except Exception as e:
        logger.error(f"Error creating training data: {str(e)}")
        return None

if __name__ == "__main__":
    # Process the dataset
    file_path = os.path.join(DATASET_DIR, 'conn.log.labeled')
    if os.path.exists(file_path):
        processed_data = process_iot23_dataset(file_path)
        
        # Create training data
        if processed_data:
            training_path = create_training_data()
            print(f"Training data created: {training_path}")
    else:
        print(f"Dataset file not found: {file_path}")
        print("Please make sure conn.log.labeled is in the server2/data/iot23/ directory")
