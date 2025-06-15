"""
IoT-23 Dataset Adapter

This module provides an adapter specifically for the IoT-23 dataset.
It normalizes the data into our standard format while preserving compatibility
with our existing system.
"""
import os
import pandas as pd
from .base_adapter import BaseAdapter
from utils.logger import get_logger

# Get logger
logger = get_logger()

class IoT23Adapter(BaseAdapter):
    """
    Adapter for the IoT-23 dataset.
    
    This adapter is specifically designed to handle the IoT-23 dataset format
    and maintain compatibility with our existing system.
    """
    
    def __init__(self):
        """Initialize the IoT-23 adapter"""
        super().__init__()
    
    def load_data(self, source_path):
        """
        Load data from an IoT-23 dataset file
        
        Args:
            source_path: Path to the IoT-23 dataset file
            
        Returns:
            Pandas DataFrame with the raw IoT-23 data
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"IoT-23 file not found: {source_path}")
        
        try:
            # IoT-23 is typically in TSV format with specific columns
            columns = [
                'ts', 'uid', 'id.orig_h', 'id.orig_p', 'id.resp_h', 'id.resp_p',
                'proto', 'service', 'duration', 'orig_bytes', 'resp_bytes',
                'conn_state', 'local_orig', 'local_resp', 'missed_bytes',
                'history', 'orig_pkts', 'orig_ip_bytes', 'resp_pkts',
                'resp_ip_bytes', 'tunnel_parents', 'label', 'detailed_label'
            ]
            
            df = pd.read_csv(source_path, sep='\t', header=None, names=columns)
            logger.info(f"Loaded IoT-23 file with {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Error loading IoT-23 file: {str(e)}")
            raise
    
    def normalize(self, raw_data):
        """
        Normalize IoT-23 data into standard format
        
        Args:
            raw_data: Pandas DataFrame with raw IoT-23 data
            
        Returns:
            Pandas DataFrame with normalized data
        """
        df = raw_data.copy()
        
        # Map IoT-23 columns to our standard schema
        normalized_df = pd.DataFrame()
        
        # Direct mappings
        normalized_df['timestamp'] = pd.to_datetime(df['ts'])
        normalized_df['src_ip'] = df['id.orig_h']
        normalized_df['dst_ip'] = df['id.resp_h']
        normalized_df['src_port'] = df['id.orig_p']
        normalized_df['dst_port'] = df['id.resp_p']
        normalized_df['protocol'] = df['proto']
        normalized_df['duration'] = df['duration']
        normalized_df['orig_bytes'] = df['orig_bytes']
        normalized_df['resp_bytes'] = df['resp_bytes']
        normalized_df['service'] = df['service']
        normalized_df['conn_state'] = df['conn_state']
        
        # Derived fields
        normalized_df['packet_size'] = df['orig_pkts'] + df['resp_pkts']
        
        # Extract device ID from source IP (last octet)
        normalized_df['device_id'] = df['id.orig_h'].apply(
            lambda ip: int(ip.split('.')[-1]) if isinstance(ip, str) else 0
        )
        
        # Handle labels
        normalized_df['label'] = df['label']
        normalized_df['attack_type'] = df['detailed_label'].fillna('normal')
        
        # Ensure all required columns exist
        normalized_df = self.ensure_schema(normalized_df)
        
        return normalized_df
