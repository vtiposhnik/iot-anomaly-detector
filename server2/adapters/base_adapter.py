"""
Base Adapter for Network Traffic Data

This module provides a base adapter class for normalizing different types of network traffic data
into a standard format that can be used by our anomaly detection models.
"""
import pandas as pd
from abc import ABC, abstractmethod
from utils.logger import get_logger

# Get logger
logger = get_logger()

class BaseAdapter(ABC):
    """
    Base class for all network traffic data adapters.
    
    This abstract class defines the interface that all adapters must implement
    to normalize different types of network traffic data into a standard format.
    """
    
    def __init__(self):
        """Initialize the adapter"""
        self.required_columns = [
            'timestamp',
            'device_id',
            'src_ip',
            'dst_ip',
            'src_port',
            'dst_port',
            'protocol',
            'packet_size',
            'duration',
            'orig_bytes',
            'resp_bytes'
        ]
        
        # Optional columns that might be present in some datasets
        self.optional_columns = [
            'service',
            'conn_state',
            'label',
            'attack_type'
        ]
    
    @abstractmethod
    def load_data(self, source_path):
        """
        Load data from the source path
        
        Args:
            source_path: Path to the data source
            
        Returns:
            Raw data in its original format
        """
        pass
    
    @abstractmethod
    def normalize(self, raw_data):
        """
        Normalize raw data into standard format
        
        Args:
            raw_data: Raw data in its original format
            
        Returns:
            Pandas DataFrame with normalized data
        """
        pass
    
    def validate_schema(self, df):
        """
        Validate that the DataFrame has the required columns
        
        Args:
            df: Pandas DataFrame to validate
            
        Returns:
            Boolean indicating if the schema is valid
        """
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        
        if missing_columns:
            logger.warning(f"Missing required columns: {missing_columns}")
            return False
        
        return True
    
    def ensure_schema(self, df):
        """
        Ensure the DataFrame has all required columns, adding defaults if needed
        
        Args:
            df: Pandas DataFrame to ensure schema for
            
        Returns:
            Pandas DataFrame with all required columns
        """
        # Add missing required columns with default values
        for col in self.required_columns:
            if col not in df.columns:
                logger.info(f"Adding missing column '{col}' with default values")
                
                # Set appropriate default values based on column type
                if col == 'timestamp':
                    df[col] = pd.Timestamp.now()
                elif col in ['src_ip', 'dst_ip', 'protocol']:
                    df[col] = 'unknown'
                elif col in ['device_id']:
                    df[col] = 0
                else:
                    df[col] = 0
        
        # Add missing optional columns with default values
        for col in self.optional_columns:
            if col not in df.columns:
                if col in ['service', 'conn_state', 'attack_type']:
                    df[col] = 'unknown'
                elif col == 'label':
                    df[col] = 'normal'
                else:
                    df[col] = None
        
        return df
    
    def process(self, source_path):
        """
        Process data from source to normalized format
        
        Args:
            source_path: Path to the data source
            
        Returns:
            Pandas DataFrame with normalized data
        """
        try:
            # Load the raw data
            raw_data = self.load_data(source_path)
            
            # Normalize the data
            normalized_data = self.normalize(raw_data)
            
            # Ensure the schema is complete
            normalized_data = self.ensure_schema(normalized_data)
            
            # Validate the final schema
            if not self.validate_schema(normalized_data):
                logger.warning("Schema validation failed after normalization")
            
            return normalized_data
            
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            raise
