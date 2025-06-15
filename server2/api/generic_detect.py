"""
Generic Anomaly Detection API

This module provides API endpoints for the generic anomaly detection system
that can work with any network traffic data.
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, status

from ml.integration import detect_anomalies_from_traffic, process_and_store_anomalies
from utils.logger import get_logger
from utils.config import get_config
from api.models import AnomalyDetectionRequest, AnomalyItem, AnomalyResponse, StatusResponse, ModelStatus, ConfigStatus
from api.dependencies import get_anomaly_detector, validate_threshold, get_pagination_params
from api.auth import get_current_active_user, check_admin_role
from api.auth.models import User

# Get logger
logger = get_logger()

# Create router
router = APIRouter(prefix="/generic", tags=["generic"])

@router.post("/detect", response_model=AnomalyResponse, status_code=status.HTTP_200_OK)
async def detect_anomalies(
    request: AnomalyDetectionRequest, 
    background_tasks: BackgroundTasks,
    anomaly_detector = Depends(get_anomaly_detector),
    threshold: float = Depends(validate_threshold),
    current_user: User = Depends(get_current_active_user)
):
    """
    Detect anomalies using the generic anomaly detection system
    
    Parameters:
        request: AnomalyDetectionRequest containing detection parameters
        background_tasks: FastAPI background tasks handler
        anomaly_detector: Anomaly detector instance from dependency
        threshold: Validated threshold from dependency
    
    Returns:
        AnomalyResponse with detected anomalies
    """
    try:
        # Get parameters from the request model
        device_id = request.device_id
        limit = request.limit
        model = request.model
        store_results = request.store_results
        
        # Use the threshold from dependency if not provided in request
        if request.threshold is not None:
            threshold = request.threshold
        
        # Detect anomalies
        anomalies = detect_anomalies_from_traffic(
            device_id=device_id,
            limit=limit,
            threshold=threshold,
            model=model
        )
        
        # Store results if requested (in background)
        if store_results and len(anomalies) > 0:
            from utils.database import insert_anomalies
            background_tasks.add_task(insert_anomalies, anomalies)
        
        # Format response
        if len(anomalies) > 0:
            # Format anomalies for response
            formatted_anomalies = []
            
            for _, row in anomalies.iterrows():
                anomaly = AnomalyItem(
                    timestamp=row['timestamp'].isoformat() if isinstance(row['timestamp'], datetime) else str(row['timestamp']),
                    device_id=str(row['device_id']),
                    src_ip=row['src_ip'],
                    dst_ip=row['dst_ip'],
                    src_port=int(row['src_port']),
                    dst_port=int(row['dst_port']),
                    protocol=row['protocol'],
                    score=float(row.get('combined_score', row.get('if_score', row.get('lof_score', 0)))),
                    model_used=model or get_config('anomaly_detection.default_model', 'both'),
                    is_genuine=True  # Initially marked as genuine
                )
                
                formatted_anomalies.append(anomaly)
            
            response = AnomalyResponse(
                status="success",
                anomalies_detected=len(formatted_anomalies),
                anomalies=formatted_anomalies
            )
        else:
            response = AnomalyResponse(
                status="success",
                anomalies_detected=0,
                anomalies=[]
            )
        
        return response
    
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )

@router.get("/status", response_model=StatusResponse, status_code=status.HTTP_200_OK)
async def get_system_status(
    anomaly_detector = Depends(get_anomaly_detector),
    current_user: User = Depends(get_current_active_user)
):
    """
    Check if the generic anomaly detection system is ready
    
    Parameters:
        anomaly_detector: Anomaly detector instance from dependency
    
    Returns:
        StatusResponse with system status information
    """
    try:
        # Models are already loaded through the dependency
        response = StatusResponse(
            status="ready",
            models=ModelStatus(
                isolation_forest=anomaly_detector.isolation_forest is not None,
                lof=anomaly_detector.lof is not None
            ),
            config=ConfigStatus(
                default_threshold=get_config('anomaly_detection.default_threshold', 0.7),
                default_model=get_config('anomaly_detection.default_model', 'both')
            )
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Error checking system status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )
