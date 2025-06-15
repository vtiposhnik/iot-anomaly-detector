"""
JSON Adapter for Network Traffic Data

This module provides an adapter for JSON files containing network traffic data.
It normalizes the data into a standard format that can be used by our anomaly detection models.
"""
import os
import json
import pandas as pd
from datetime import datetime
from .base_adapter import BaseAdapter
from utils.logger import get_logger

# Get logger
logger = get_logger()

class JSONAdapter(BaseAdapter):
    """
    Adapter for JSON files containing network traffic data.
    
    This adapter can handle various JSON formats, including arrays of objects
    and nested JSON structures.
    """
    
    def __init__(self, field_mapping=None, json_path=None):
        """
        Initialize the JSON adapter
        
        Args:
            field_mapping: Dictionary mapping JSON fields to standard columns
                          If None, will attempt to auto-detect
            json_path: Path to the relevant data within the JSON structure
                      (e.g., 'data.flows' for nested data)
        """
        super().__init__()
        self.field_mapping = field_mapping or {}
        self.json_path = json_path
    
    def load_data(self, source_path):
        """
        Load data from a JSON file
        
        Args:
            source_path: Path to the JSON file
            
        Returns:
            Dictionary or list containing the raw JSON data
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"JSON file not found: {source_path}")
        
        try:
            with open(source_path, 'r') as f:
                data = json.load(f)
            
            # Navigate to the specified path if provided
            if self.json_path:
                path_parts = self.json_path.split('.')
                for part in path_parts:
                    if part in data:
                        data = data[part]
                    else:
                        logger.warning(f"JSON path '{part}' not found in data")
                        break
            
            logger.info(f"Loaded JSON data: {type(data)}")
            return data
        except Exception as e:
            logger.error(f"Error loading JSON file: {str(e)}")
            raise
    
    def _extract_value(self, obj, field, default=None):
        """
        Extract a value from a nested JSON object using dot notation
        
        Args:
            obj: JSON object
            field: Field name, can use dot notation for nested fields
            default: Default value if field is not found
            
        Returns:
            Extracted value or default
        """
        if '.' in field:
            parts = field.split('.', 1)
            if parts[0] in obj and isinstance(obj[parts[0]], dict):
                return self._extract_value(obj[parts[0]], parts[1], default)
            return default
        return obj.get(field, default)
    
    def _auto_detect_mapping(self, data):
        """
        Attempt to automatically detect field mapping from JSON data
        
        Args:
            data: JSON data (list of objects or single object)
            
        Returns:
            Dictionary mapping JSON fields to standard columns
        """
        mapping = {}
        
        # Get a sample object
        sample = data[0] if isinstance(data, list) and data else data
        
        if not isinstance(sample, dict):
            logger.warning("Cannot auto-detect mapping from non-object JSON data")
            return mapping
        
        # Flatten the sample object to handle nested structures
        flat_sample = {}
        
        def flatten(obj, prefix=''):
            for key, value in obj.items():
                if isinstance(value, dict):
                    flatten(value, f"{prefix}{key}.")
                else:
                    flat_sample[f"{prefix}{key}"] = value
        
        flatten(sample)
        
        # Common variations of field names
        common_mappings = {
            'timestamp': ['timestamp', 'time', 'date', 'datetime', 'ts', 'startTime', 'endTime'],
            'device_id': ['device_id', 'device', 'deviceId', 'id', 'host', 'hostId', 'sourceId'],
            'src_ip': ['src_ip', 'source_ip', 'srcIp', 'sourceIp', 'src', 'source', 'ipv4_src_addr'],
            'dst_ip': ['dst_ip', 'destination_ip', 'dstIp', 'destinationIp', 'dst', 'destination', 'ipv4_dst_addr'],
            'src_port': ['src_port', 'source_port', 'srcPort', 'sourcePort', 'sport', 'l4_src_port'],
            'dst_port': ['dst_port', 'destination_port', 'dstPort', 'destinationPort', 'dport', 'l4_dst_port'],
            'protocol': ['protocol', 'proto', 'protocolId', 'protocolName', 'l4_proto'],
            'packet_size': ['packet_size', 'packetSize', 'size', 'bytes', 'octets', 'in_bytes', 'out_bytes'],
            'duration': ['duration', 'dur', 'flowDuration', 'flow_duration', 'elapsed', 'timeElapsed'],
            'orig_bytes': ['orig_bytes', 'origBytes', 'bytesOut', 'out_bytes', 'sentBytes', 'bytes_sent'],
            'resp_bytes': ['resp_bytes', 'respBytes', 'bytesIn', 'in_bytes', 'receivedBytes', 'bytes_received']
        }
        
        # Try to find matches for each standard column
        for std_col, variations in common_mappings.items():
            for var in variations:
                # Check for exact match in flattened keys
                if var in flat_sample:
                    mapping[std_col] = var
                    break
                
                # Check for case-insensitive match
                for key in flat_sample.keys():
                    if key.lower() == var.lower():
                        mapping[std_col] = key
                        break
        
        return mapping
    
    def normalize(self, raw_data):
        """
        Normalize JSON data into standard format
        
        Args:
            raw_data: Dictionary or list containing the raw JSON data
            
        Returns:
            Pandas DataFrame with normalized data
        """
        data = raw_data
        
        # Convert to list if it's a single object
        if isinstance(data, dict):
            data = [data]
        
        # Ensure data is a list
        if not isinstance(data, list):
            raise ValueError("JSON data must be an array of objects or a single object")
        
        # Auto-detect mapping if not provided
        if not self.field_mapping:
            self.field_mapping = self._auto_detect_mapping(data)
            logger.info(f"Auto-detected field mapping: {self.field_mapping}")
        
        # Extract data according to the mapping
        normalized_data = []
        
        for item in data:
            normalized_item = {}
            
            for std_col, json_field in self.field_mapping.items():
                value = self._extract_value(item, json_field)
                normalized_item[std_col] = value
            
            normalized_data.append(normalized_item)
        
        # Create DataFrame
        df = pd.DataFrame(normalized_data)
        
        # Handle timestamp conversion if needed
        if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            except:
                logger.warning("Could not convert timestamp column to datetime")
                df['timestamp'] = pd.Timestamp.now()
        
        # Ensure all required columns exist
        df = self.ensure_schema(df)
        
        return df
