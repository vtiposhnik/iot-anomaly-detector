"""
Integration Module for Anomaly Detection Systems

This module provides functions to integrate the new generic anomaly detection system
with the existing API endpoints and database structure.
"""
import os
import pandas as pd
from datetime import datetime
from adapters.adapter_factory import create_adapter
from ml.generic_anomaly_detector import detect_anomalies
from utils.logger import get_logger
from utils.config import get_config
from utils.database import get_traffic, insert_anomalies

# Get logger
logger = get_logger()

def detect_anomalies_from_traffic(traffic_data=None, device_id=None, limit=100, threshold=None, model=None):
    """
    Detect anomalies in traffic data using the generic anomaly detection system
    
    Args:
        traffic_data: Optional DataFrame with traffic data (if None, will load from database)
        device_id: Optional device ID to filter traffic data
        limit: Maximum number of traffic records to process
        threshold: Threshold for anomaly detection (if None, use default from config)
        model: Model to use (if None, use default from config)
        
    Returns:
        DataFrame with detected anomalies
    """
    try:
        # Get default values from config
        if threshold is None:
            threshold = get_config('anomaly_detection.default_threshold', 0.7)
        
        if model is None:
            model = get_config('anomaly_detection.default_model', 'both')
        
        # Load traffic data if not provided
        if traffic_data is None:
            logger.info(f"Loading traffic data from database (limit={limit})")
            traffic_data = get_traffic(limit=limit)
            
            # Convert to DataFrame if it's a list of dictionaries
            if isinstance(traffic_data, list):
                traffic_data = pd.DataFrame(traffic_data)
        
        # Filter by device ID if provided
        if device_id is not None:
            traffic_data = traffic_data[traffic_data['device_id'] == device_id]
        
        # Check if we have data to process
        if len(traffic_data) == 0:
            logger.warning("No traffic data to process")
            return pd.DataFrame()
        
        # Normalize column names to match our standard schema
        column_mapping = {
            'log_id': 'log_id',
            'device_id': 'device_id',
            'timestamp': 'timestamp',
            'source_ip': 'src_ip',
            'source_port': 'src_port',
            'dest_ip': 'dst_ip',
            'dest_port': 'dst_port',
            'protocol': 'protocol',
            'service': 'service',
            'duration': 'duration',
            'orig_bytes': 'orig_bytes',
            'resp_bytes': 'resp_bytes',
            'conn_state': 'conn_state',
            'packet_size': 'packet_size'
        }
        
        # Create a new DataFrame with normalized column names
        normalized_data = pd.DataFrame()
        
        for std_col, db_col in column_mapping.items():
            if db_col in traffic_data.columns:
                normalized_data[std_col] = traffic_data[db_col]
            else:
                # Set default values for missing columns
                if std_col == 'timestamp':
                    normalized_data[std_col] = pd.Timestamp.now()
                elif std_col in ['src_ip', 'dst_ip', 'protocol', 'service', 'conn_state']:
                    normalized_data[std_col] = 'unknown'
                else:
                    normalized_data[std_col] = 0
        
        # Detect anomalies
        logger.info(f"Detecting anomalies in {len(normalized_data)} traffic records "
                   f"(threshold={threshold}, model={model})")
        
        result = detect_anomalies(normalized_data, threshold, model)
        
        # Extract anomalies
        anomalies = result[result['is_anomaly']].copy()
        
        logger.info(f"Detected {len(anomalies)} anomalies")
        
        return anomalies
    
    except Exception as e:
        logger.error(f"Error detecting anomalies from traffic: {str(e)}")
        return pd.DataFrame()

def detect_anomalies_from_file(file_path, adapter_type=None, device_id=None, threshold=None, model=None, store_results=True):
    """
    Detect anomalies in a file using the generic anomaly detection system
    
    Args:
        file_path: Path to the file containing traffic data
        adapter_type: Type of adapter to use (csv, json, pcap, iot23)
        device_id: Optional device ID to associate with the data
        threshold: Threshold for anomaly detection (if None, use default from config)
        model: Model to use (if None, use default from config)
        store_results: Whether to store results in the database
        
    Returns:
        DataFrame with detected anomalies
    """
    try:
        # Get default values from config
        if threshold is None:
            threshold = get_config('anomaly_detection.default_threshold', 0.7)
        
        if model is None:
            model = get_config('anomaly_detection.default_model', 'both')
        
        # Determine adapter type if not provided
        if adapter_type is None:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.csv':
                adapter_type = 'csv'
            elif file_ext == '.json':
                adapter_type = 'json'
            elif file_ext in ['.pcap', '.pcapng']:
                adapter_type = 'pcap'
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
        
        logger.info(f"Loading data from {file_path} using {adapter_type} adapter")
        
        # Create adapter and load data
        adapter = create_adapter(adapter_type)
        normalized_data = adapter.load_and_normalize(file_path)
        
        # Set device ID if provided
        if device_id is not None:
            normalized_data['device_id'] = device_id
        
        # Detect anomalies
        logger.info(f"Detecting anomalies in {len(normalized_data)} traffic records "  
                   f"(threshold={threshold}, model={model})")
        
        result = detect_anomalies(normalized_data, threshold, model)
        
        # Extract anomalies
        anomalies = result[result['is_anomaly']].copy()
        
        logger.info(f"Detected {len(anomalies)} anomalies")
        
        # Store anomalies if requested
        if store_results and len(anomalies) > 0:
            count = insert_anomalies(anomalies)
            logger.info(f"Stored {count} anomalies in database")
        
        return anomalies
    
    except Exception as e:
        logger.error(f"Error detecting anomalies from file: {str(e)}")
        raise

def process_and_store_anomalies(traffic_data=None, device_id=None, limit=100, threshold=None, model=None):
    """
    Process traffic data, detect anomalies, and store them in the database
    
    Args:
        traffic_data: Optional DataFrame with traffic data (if None, will load from database)
        device_id: Optional device ID to filter traffic data
        limit: Maximum number of traffic records to process
        threshold: Threshold for anomaly detection (if None, use default from config)
        model: Model to use (if None, use default from config)
        
    Returns:
        Number of anomalies detected and stored
    """
    try:
        # Detect anomalies
        anomalies = detect_anomalies_from_traffic(
            traffic_data=traffic_data,
            device_id=device_id,
            limit=limit,
            threshold=threshold,
            model=model
        )
        
        # Check if we detected any anomalies
        if len(anomalies) == 0:
            logger.info("No anomalies detected")
            return 0
        
        # Store anomalies in database
        count = insert_anomalies(anomalies)
        
        logger.info(f"Stored {count} anomalies in database")
        
        return count
    
    except Exception as e:
        logger.error(f"Error processing and storing anomalies: {str(e)}")
        return 0
