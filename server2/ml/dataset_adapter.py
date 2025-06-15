"""
IoT-23 Dataset Adapter for Anomaly Detection Models

This module adapts our anomaly detection models to work with the IoT-23 dataset.
It provides functions for feature extraction and preprocessing specific to network traffic data.
"""
import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from utils.logger import get_logger

# Get logger
logger = get_logger()

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')

def extract_features_from_traffic(traffic_data):
    """
    Extract features from network traffic data for anomaly detection
    
    Args:
        traffic_data: DataFrame containing network traffic data
    
    Returns:
        DataFrame with extracted features
    """
    try:
        # Make a copy to avoid modifying the original
        df = traffic_data.copy()
        
        # Basic features from traffic data
        features = [
            'device_id', 'packet_size', 'duration', 'orig_bytes', 'resp_bytes'
        ]
        
        # Check if all required features exist
        for feature in features:
            if feature not in df.columns:
                logger.warning(f"Feature '{feature}' not found in traffic data")
                df[feature] = 0
        
        # Extract additional features if possible
        
        # 1. Bytes ratio (if both orig and resp bytes are available)
        if 'orig_bytes' in df.columns and 'resp_bytes' in df.columns:
            # Avoid division by zero
            df['bytes_ratio'] = df.apply(
                lambda row: row['orig_bytes'] / max(row['resp_bytes'], 1) 
                if row['orig_bytes'] > 0 and row['resp_bytes'] > 0 
                else 0, 
                axis=1
            )
        
        # 2. Packet rate (packets per second)
        if 'packet_size' in df.columns and 'duration' in df.columns:
            df['packet_rate'] = df.apply(
                lambda row: row['packet_size'] / max(row['duration'], 0.001)
                if row['duration'] > 0
                else 0,
                axis=1
            )
        
        # 3. Traffic direction features
        if 'source_port' in df.columns and 'dest_port' in df.columns:
            # Is this traffic on a well-known port?
            df['is_well_known_port'] = df.apply(
                lambda row: 1 if (int(row['source_port']) < 1024 or int(row['dest_port']) < 1024) else 0,
                axis=1
            )
        
        # 4. Protocol features
        if 'protocol' in df.columns:
            # One-hot encode the protocol
            protocols = ['tcp', 'udp', 'icmp']
            for protocol in protocols:
                df[f'protocol_{protocol}'] = df['protocol'].apply(
                    lambda x: 1 if str(x).lower() == protocol else 0
                )
        
        # 5. Service features
        if 'service' in df.columns:
            # One-hot encode common services
            common_services = ['http', 'dns', 'ssh', 'smtp', 'ftp']
            for service in common_services:
                df[f'service_{service}'] = df['service'].apply(
                    lambda x: 1 if x and service in str(x).lower() else 0
                )
        
        # 6. Connection state features
        if 'conn_state' in df.columns:
            # One-hot encode connection states
            conn_states = ['S0', 'S1', 'SF', 'REJ', 'S2', 'S3', 'RSTO', 'RSTR']
            for state in conn_states:
                df[f'conn_state_{state}'] = df['conn_state'].apply(
                    lambda x: 1 if x == state else 0
                )
        
        # Get all numeric columns for features
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Remove any non-feature columns
        exclude_cols = ['log_id', 'link_id', 'is_anomaly']
        feature_cols = [col for col in numeric_cols if col not in exclude_cols]
        
        # Create feature DataFrame
        feature_df = df[feature_cols].copy()
        
        # Add label if available
        if 'is_anomaly' in df.columns:
            feature_df['is_anomaly'] = df['is_anomaly']
        
        logger.info(f"Extracted {len(feature_cols)} features from traffic data")
        return feature_df
    
    except Exception as e:
        logger.error(f"Error extracting features: {str(e)}")
        return pd.DataFrame()

def normalize_features(features, training=False):
    """
    Normalize features for model training/inference
    
    Args:
        features: DataFrame containing features
        training: Boolean indicating if this is for training (will fit scaler)
    
    Returns:
        Normalized features as numpy array
    """
    try:
        # Make a copy to avoid modifying the original
        df = features.copy()
        
        # Remove label column if present
        label_col = None
        if 'is_anomaly' in df.columns:
            label_col = df['is_anomaly']
            df = df.drop('is_anomaly', axis=1)
        
        # Get feature names
        feature_names = df.columns.tolist()
        
        # Convert to numpy array
        X = df.values
        
        # Initialize scaler
        scaler = StandardScaler()
        
        # Fit or transform
        if training:
            X_scaled = scaler.fit_transform(X)
            
            # Save the scaler
            scaler_path = os.path.join(MODEL_DIR, 'iot23_scaler.pkl')
            os.makedirs(os.path.dirname(scaler_path), exist_ok=True)
            
            import pickle
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f)
            
            logger.info(f"Saved feature scaler to {scaler_path}")
        else:
            # Load the scaler if it exists
            scaler_path = os.path.join(MODEL_DIR, 'iot23_scaler.pkl')
            
            if os.path.exists(scaler_path):
                import pickle
                with open(scaler_path, 'rb') as f:
                    scaler = pickle.load(f)
                
                X_scaled = scaler.transform(X)
            else:
                # If no scaler exists, just standardize without saving
                X_scaled = scaler.fit_transform(X)
        
        # Return normalized features and optionally the label
        if label_col is not None:
            return X_scaled, label_col.values, feature_names
        else:
            return X_scaled, None, feature_names
    
    except Exception as e:
        logger.error(f"Error normalizing features: {str(e)}")
        if 'is_anomaly' in features.columns:
            return np.array([]), features['is_anomaly'].values, []
        else:
            return np.array([]), None, []

def prepare_iot23_training_data():
    """
    Prepare IoT-23 data for training anomaly detection models
    
    Returns:
        Tuple of (X_train, y_train, feature_names)
    """
    try:
        # Load processed traffic data
        traffic_path = os.path.join(PROCESSED_DIR, 'traffic.csv')
        anomalies_path = os.path.join(PROCESSED_DIR, 'anomalies.csv')
        
        if not os.path.exists(traffic_path) or not os.path.exists(anomalies_path):
            logger.error("Processed data not found. Run dataset_processor.py first.")
            return None, None, None
        
        # Load traffic data
        traffic_df = pd.read_csv(traffic_path)
        anomalies_df = pd.read_csv(anomalies_path)
        
        # Create a set of anomalous log_ids
        anomalous_logs = set(anomalies_df['log_id']) if not anomalies_df.empty else set()
        
        # Add a label column to the traffic data
        traffic_df['is_anomaly'] = traffic_df['log_id'].apply(lambda x: x in anomalous_logs)
        
        # Extract features
        feature_df = extract_features_from_traffic(traffic_df)
        
        if feature_df.empty:
            logger.error("Failed to extract features from traffic data")
            return None, None, None
        
        # Normalize features
        X_normalized, y, feature_names = normalize_features(feature_df, training=True)
        
        logger.info(f"Prepared {len(X_normalized)} samples for training")
        logger.info(f"Anomalies: {sum(y if y is not None else 0)}")
        
        return X_normalized, y, feature_names
    
    except Exception as e:
        logger.error(f"Error preparing IoT-23 training data: {str(e)}")
        return None, None, None

def load_iot23_test_data(limit=1000):
    """
    Load a subset of IoT-23 data for testing/evaluation
    
    Args:
        limit: Maximum number of samples to load
    
    Returns:
        Tuple of (X_test, y_test, feature_names)
    """
    try:
        # Load processed traffic data
        traffic_path = os.path.join(PROCESSED_DIR, 'traffic.csv')
        anomalies_path = os.path.join(PROCESSED_DIR, 'anomalies.csv')
        
        if not os.path.exists(traffic_path) or not os.path.exists(anomalies_path):
            logger.error("Processed data not found. Run dataset_processor.py first.")
            return None, None, None
        
        # Load traffic data (limit to specified number of samples)
        traffic_df = pd.read_csv(traffic_path).sample(min(limit, pd.read_csv(traffic_path).shape[0]))
        anomalies_df = pd.read_csv(anomalies_path)
        
        # Create a set of anomalous log_ids
        anomalous_logs = set(anomalies_df['log_id']) if not anomalies_df.empty else set()
        
        # Add a label column to the traffic data
        traffic_df['is_anomaly'] = traffic_df['log_id'].apply(lambda x: x in anomalous_logs)
        
        # Extract features
        feature_df = extract_features_from_traffic(traffic_df)
        
        if feature_df.empty:
            logger.error("Failed to extract features from traffic data")
            return None, None, None
        
        # Normalize features
        X_normalized, y, feature_names = normalize_features(feature_df, training=False)
        
        logger.info(f"Loaded {len(X_normalized)} samples for testing")
        logger.info(f"Anomalies: {sum(y if y is not None else 0)}")
        
        return X_normalized, y, feature_names
    
    except Exception as e:
        logger.error(f"Error loading IoT-23 test data: {str(e)}")
        return None, None, None

if __name__ == "__main__":
    # Test the module
    X_train, y_train, feature_names = prepare_iot23_training_data()
    
    if X_train is not None:
        print(f"Prepared {len(X_train)} training samples with {len(feature_names)} features")
        print(f"Feature names: {feature_names}")
        
        # Load test data
        X_test, y_test, _ = load_iot23_test_data(limit=100)
        
        if X_test is not None:
            print(f"Loaded {len(X_test)} test samples")
