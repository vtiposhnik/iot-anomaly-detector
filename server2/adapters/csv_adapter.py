"""
CSV Adapter for Network Traffic Data

This module provides an adapter for CSV files containing network traffic data.
It normalizes the data into a standard format that can be used by our anomaly detection models.
"""
import os
import pandas as pd
from datetime import datetime
from .base_adapter import BaseAdapter
from utils.logger import get_logger

# Get logger
logger = get_logger()

class CSVAdapter(BaseAdapter):
    """
    Adapter for CSV files containing network traffic data.
    
    This adapter can handle various CSV formats by mapping columns
    to our standard schema.
    """
    
    def __init__(self, column_mapping=None):
        """
        Initialize the CSV adapter
        
        Args:
            column_mapping: Dictionary mapping CSV columns to standard columns
                            If None, will attempt to auto-detect
        """
        super().__init__()
        self.column_mapping = column_mapping or {}
    
    def load_data(self, source_path):
        """
        Load data from a CSV file
        
        Args:
            source_path: Path to the CSV file
            
        Returns:
            Pandas DataFrame with the raw CSV data
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"CSV file not found: {source_path}")
        
        try:
            # Try to infer datetime format if possible
            df = pd.read_csv(source_path, parse_dates=True, infer_datetime_format=True)
            logger.info(f"Loaded CSV file with {len(df)} rows and {len(df.columns)} columns")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV file: {str(e)}")
            raise
    
    def _auto_detect_mapping(self, df):
        """
        Attempt to automatically detect column mapping
        
        Args:
            df: Pandas DataFrame with raw CSV data
            
        Returns:
            Dictionary mapping CSV columns to standard columns
        """
        mapping = {}
        columns = df.columns
        
        # Common variations of column names
        common_mappings = {
            'timestamp': ['timestamp', 'time', 'date', 'datetime', 'ts'],
            'device_id': ['device_id', 'device', 'deviceid', 'id', 'host', 'host_id'],
            'src_ip': ['src_ip', 'source_ip', 'src', 'source', 'id.orig_h'],
            'dst_ip': ['dst_ip', 'destination_ip', 'dst', 'destination', 'id.resp_h'],
            'src_port': ['src_port', 'source_port', 'sport', 'id.orig_p'],
            'dst_port': ['dst_port', 'destination_port', 'dport', 'id.resp_p'],
            'protocol': ['protocol', 'proto', 'prot', 'proto_name'],
            'packet_size': ['packet_size', 'size', 'pkt_size', 'packets'],
            'duration': ['duration', 'dur', 'time_delta', 'elapsed'],
            'orig_bytes': ['orig_bytes', 'orig_pkts', 'bytes_out', 'sent_bytes'],
            'resp_bytes': ['resp_bytes', 'resp_pkts', 'bytes_in', 'received_bytes'],
            'service': ['service', 'svc', 'app_protocol'],
            'conn_state': ['conn_state', 'state', 'connection_state'],
            'label': ['label', 'class', 'is_anomaly', 'is_attack'],
            'attack_type': ['attack_type', 'attack', 'attack_class']
        }
        
        # Try to find matches for each standard column
        for std_col, variations in common_mappings.items():
            for var in variations:
                # Check for exact match
                if var in columns:
                    mapping[std_col] = var
                    break
                
                # Check for case-insensitive match
                for col in columns:
                    if col.lower() == var:
                        mapping[std_col] = col
                        break
        
        return mapping
    
    def normalize(self, raw_data):
        """
        Normalize CSV data into standard format
        
        Args:
            raw_data: Pandas DataFrame with raw CSV data
            
        Returns:
            Pandas DataFrame with normalized data
        """
        df = raw_data.copy()
        
        # Auto-detect mapping if not provided
        if not self.column_mapping:
            self.column_mapping = self._auto_detect_mapping(df)
            logger.info(f"Auto-detected column mapping: {self.column_mapping}")
        
        # Create a new DataFrame with the standard schema
        normalized_df = pd.DataFrame()
        
        # Map columns according to the mapping
        for std_col, csv_col in self.column_mapping.items():
            if csv_col in df.columns:
                normalized_df[std_col] = df[csv_col]
        
        # Handle timestamp conversion if needed
        if 'timestamp' in normalized_df.columns and not pd.api.types.is_datetime64_any_dtype(normalized_df['timestamp']):
            try:
                normalized_df['timestamp'] = pd.to_datetime(normalized_df['timestamp'])
            except:
                logger.warning("Could not convert timestamp column to datetime")
                normalized_df['timestamp'] = pd.Timestamp.now()
        
        # Ensure all required columns exist
        normalized_df = self.ensure_schema(normalized_df)
        
        return normalized_df
