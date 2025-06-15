"""
API Dependencies

This module contains FastAPI dependency functions for common operations.
"""
from typing import Optional
from fastapi import Depends, HTTPException, Query, status
from utils.logger import get_logger
from utils.database import get_devices, get_traffic, get_anomalies
from ml.generic_anomaly_detector import anomaly_detector

# Get logger
logger = get_logger()

async def get_device_by_id(device_id: int):
    """
    Dependency to get a device by ID
    
    Args:
        device_id: The ID of the device to retrieve
        
    Returns:
        The device if found
        
    Raises:
        HTTPException: If the device is not found
    """
    devices = get_devices(limit=1000)
    for device in devices:
        if device['device_id'] == device_id:
            return device
    
    # If we get here, the device was not found
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Device with ID {device_id} not found"
    )

async def get_pagination_params(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return")
):
    """
    Dependency to get pagination parameters
    
    Args:
        skip: Number of items to skip
        limit: Maximum number of items to return
        
    Returns:
        Tuple of (skip, limit)
    """
    return (skip, limit)

async def get_anomaly_detector():
    """
    Dependency to get the anomaly detector
    
    Returns:
        The anomaly detector instance
        
    Raises:
        HTTPException: If the anomaly detector is not ready
    """
    # Check if models are loaded
    if not anomaly_detector._load_models():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Anomaly detection models are not ready. Please train the models first."
        )
    
    return anomaly_detector

async def validate_threshold(
    threshold: Optional[float] = Query(None, ge=0.0, le=1.0, description="Anomaly detection threshold")
):
    """
    Dependency to validate the threshold parameter
    
    Args:
        threshold: Anomaly detection threshold
        
    Returns:
        The validated threshold
    """
    from utils.config import get_config
    
    # If threshold is not provided, use the default from config
    if threshold is None:
        threshold = get_config('anomaly_detection.default_threshold', 0.7)
    
    return threshold
