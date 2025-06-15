"""
Adapter Factory for Network Traffic Data

This module provides a factory for creating the appropriate adapter
based on the type of network traffic data.
"""
import os
from utils.logger import get_logger
from .csv_adapter import CSVAdapter
from .json_adapter import JSONAdapter
from .pcap_adapter import PCAPAdapter
from .iot23_adapter import IoT23Adapter
from .mqtt_adapter import MQTTAdapter

# Get logger
logger = get_logger()

def create_adapter(source_path, adapter_type=None, **kwargs):
    """
    Create an appropriate adapter based on the source path or specified type
    
    Args:
        source_path: Path to the data source
        adapter_type: Explicitly specified adapter type (optional)
                     If None, will be inferred from file extension
        **kwargs: Additional arguments to pass to the adapter constructor
        
    Returns:
        An adapter instance
    """
    # Special case for MQTT adapter which doesn't need a file source
    if adapter_type and adapter_type.lower() == 'mqtt':
        logger.info(f"Creating MQTT adapter with broker: {kwargs.get('broker_host', 'localhost')}")
        return MQTTAdapter(**kwargs)
        
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source file not found: {source_path}")
    
    # If adapter type is explicitly specified, use that
    if adapter_type:
        return _create_adapter_by_type(adapter_type, **kwargs)
    
    # Otherwise, infer from file extension
    file_ext = os.path.splitext(source_path)[1].lower()
    
    if file_ext == '.csv':
        logger.info(f"Creating CSV adapter for {source_path}")
        return CSVAdapter(**kwargs)
    elif file_ext in ['.json', '.jsonl']:
        logger.info(f"Creating JSON adapter for {source_path}")
        return JSONAdapter(**kwargs)
    elif file_ext in ['.pcap', '.pcapng', '.cap']:
        logger.info(f"Creating PCAP adapter for {source_path}")
        return PCAPAdapter(**kwargs)
    elif file_ext in ['.log', '.tsv'] or 'conn.log' in source_path:
        logger.info(f"Creating IoT-23 adapter for {source_path}")
        return IoT23Adapter(**kwargs)
    else:
        logger.warning(f"Unknown file extension: {file_ext}, defaulting to CSV adapter")
        return CSVAdapter(**kwargs)

def _create_adapter_by_type(adapter_type, **kwargs):
    """
    Create an adapter by explicitly specified type
    
    Args:
        adapter_type: Type of adapter to create ('csv', 'json', 'pcap', 'iot23', 'mqtt')
        **kwargs: Additional arguments to pass to the adapter constructor
        
    Returns:
        An adapter instance
    """
    adapter_type = adapter_type.lower()
    
    if adapter_type == 'csv':
        return CSVAdapter(**kwargs)
    elif adapter_type == 'json':
        return JSONAdapter(**kwargs)
    elif adapter_type == 'pcap':
        return PCAPAdapter(**kwargs)
    elif adapter_type == 'iot23':
        return IoT23Adapter(**kwargs)
    elif adapter_type == 'mqtt':
        return MQTTAdapter(**kwargs)
    else:
        raise ValueError(f"Unknown adapter type: {adapter_type}")
