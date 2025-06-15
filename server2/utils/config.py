"""
Configuration Utility

This module provides functions for loading and accessing configuration settings.
"""
import os
import yaml
from utils.logger import get_logger

# Get logger
logger = get_logger()

# Constants
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yml')

# Global configuration
_config = None

def load_config():
    """
    Load configuration from YAML file
    
    Returns:
        Dictionary containing configuration
    """
    global _config
    
    try:
        # Check if config is already loaded
        if _config is not None:
            return _config
        
        # Check if config file exists
        if not os.path.exists(CONFIG_PATH):
            logger.warning(f"Configuration file not found: {CONFIG_PATH}")
            _config = {}
            return _config
        
        # Load config from file
        with open(CONFIG_PATH, 'r') as f:
            _config = yaml.safe_load(f)
        
        logger.info(f"Loaded configuration from {CONFIG_PATH}")
        return _config
    
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        _config = {}
        return _config

def get_config(path=None, default=None):
    """
    Get configuration value by path
    
    Args:
        path: Dot-separated path to configuration value (e.g., 'database.path')
        default: Default value if path not found
    
    Returns:
        Configuration value or default
    """
    # Load config if not already loaded
    config = load_config()
    
    # Return entire config if no path specified
    if path is None:
        return config
    
    # Split path into parts
    parts = path.split('.')
    
    # Navigate through config
    current = config
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    
    return current

# Load configuration on module import
load_config()
