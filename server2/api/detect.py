"""
Anomaly Detection API

This module provides API endpoints for detecting anomalies in network traffic data
from any source.
"""
import os
import json
from flask import Blueprint, request, jsonify
from datetime import datetime
import pandas as pd
from adapters.adapter_factory import create_adapter
from ml.generic_anomaly_detector import detect_anomalies
from utils.logger import get_logger
from utils.database import insert_anomalies

# Get logger
logger = get_logger()

# Create blueprint
detect_bp = Blueprint('detect', __name__)

@detect_bp.route('/detect', methods=['POST'])
def detect():
    """
    Detect anomalies in network traffic data
    
    Request body:
    {
        "path": "path/to/data/file",  # Path to data file (optional)
        "data": [...],                # Raw data as JSON (optional)
        "adapter": "csv",             # Adapter type (optional)
        "threshold": 0.7,             # Anomaly threshold (optional)
        "model": "both"               # Model to use (optional)
    }
    
    Returns:
        JSON response with detected anomalies
    """
    try:
        # Get request data
        req_data = request.get_json()
        
        if not req_data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get parameters
        path = req_data.get('path')
        data = req_data.get('data')
        adapter_type = req_data.get('adapter')
        threshold = req_data.get('threshold')
        model = req_data.get('model', 'both')
        
        # Validate parameters
        if not path and not data:
            return jsonify({'error': 'Either path or data must be provided'}), 400
        
        # Process data
        if path:
            # Check if file exists
            if not os.path.exists(path):
                return jsonify({'error': f'File not found: {path}'}), 404
            
            # Create adapter and process data
            adapter = create_adapter(path, adapter_type)
            normalized_data = adapter.process(path)
        
        else:
            # Create adapter for raw data
            if adapter_type:
                adapter = create_adapter('dummy.json', adapter_type)
            else:
                adapter = create_adapter('dummy.json', 'json')
            
            # Convert data to DataFrame
            if isinstance(data, list):
                raw_data = pd.DataFrame(data)
            else:
                raw_data = pd.DataFrame([data])
            
            # Normalize data
            normalized_data = adapter.normalize(raw_data)
            normalized_data = adapter.ensure_schema(normalized_data)
        
        # Detect anomalies
        result = detect_anomalies(normalized_data, threshold, model)
        
        # Extract anomalies
        anomalies = result[result['is_anomaly']].copy()
        
        # Format response
        if len(anomalies) > 0:
            # Store anomalies in database
            insert_anomalies(anomalies)
            
            # Format anomalies for response
            formatted_anomalies = []
            
            for _, row in anomalies.iterrows():
                anomaly = {
                    'timestamp': row['timestamp'].isoformat() if isinstance(row['timestamp'], datetime) else str(row['timestamp']),
                    'device_id': str(row['device_id']),
                    'src_ip': row['src_ip'],
                    'dst_ip': row['dst_ip'],
                    'src_port': int(row['src_port']),
                    'dst_port': int(row['dst_port']),
                    'protocol': row['protocol'],
                    'score': float(row.get('combined_score', row.get('if_score', row.get('lof_score', 0)))),
                    'model_used': model,
                    'is_genuine': True  # Initially marked as genuine
                }
                
                formatted_anomalies.append(anomaly)
            
            response = {
                'status': 'success',
                'anomalies_detected': len(formatted_anomalies),
                'anomalies': formatted_anomalies
            }
        else:
            response = {
                'status': 'success',
                'anomalies_detected': 0,
                'anomalies': []
            }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")
        return jsonify({'error': str(e)}), 500

@detect_bp.route('/detect/status', methods=['GET'])
def status():
    """
    Check if anomaly detection models are loaded
    
    Returns:
        JSON response with model status
    """
    try:
        # Import here to avoid circular imports
        from ml.generic_anomaly_detector import anomaly_detector
        
        # Check if models are loaded
        models_loaded = anomaly_detector._load_models()
        
        response = {
            'status': 'ready' if models_loaded else 'not_ready',
            'models': {
                'isolation_forest': anomaly_detector.isolation_forest is not None,
                'lof': anomaly_detector.lof is not None
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error checking model status: {str(e)}")
        return jsonify({'error': str(e)}), 500
