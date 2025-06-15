"""
File Upload API

This module provides API endpoints for uploading files for anomaly detection.
"""
import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse

from utils.logger import get_logger
from utils.config import get_config
from api.models import AnomalyResponse, AnomalyItem
from api.dependencies import get_anomaly_detector, validate_threshold
from api.auth import get_current_active_user, check_admin_role
from api.auth.models import User
from adapters.adapter_factory import create_adapter
from ml.integration import detect_anomalies_from_file

# Get logger
logger = get_logger()

# Create router
router = APIRouter(prefix="/files", tags=["file-upload"])

@router.post("/upload", response_model=AnomalyResponse)
async def upload_file_for_detection(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    device_id: Optional[int] = Form(None),
    threshold: Optional[float] = Depends(validate_threshold),
    model: Optional[str] = Form("both"),
    store_results: bool = Form(True),
    anomaly_detector = Depends(get_anomaly_detector),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a file for anomaly detection
    
    Parameters:
        background_tasks: FastAPI background tasks handler
        file: The file to upload (CSV, JSON, PCAP)
        device_id: Optional device ID to associate with the data
        threshold: Anomaly detection threshold
        model: Model to use (isolation_forest, lof, both)
        store_results: Whether to store results in the database
        anomaly_detector: Anomaly detector instance from dependency
    
    Returns:
        AnomalyResponse with detected anomalies
    """
    try:
        # Create upload directory if it doesn't exist
        upload_dir = get_config('paths.upload_dir', 'data/uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Determine file type from extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        adapter_type = None
        
        if file_ext == '.csv':
            adapter_type = 'csv'
        elif file_ext == '.json':
            adapter_type = 'json'
        elif file_ext in ['.pcap', '.pcapng']:
            adapter_type = 'pcap'
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {file_ext}. Supported types: .csv, .json, .pcap, .pcapng"
            )
        
        # Process file in background
        def process_file():
            try:
                # Detect anomalies
                anomalies = detect_anomalies_from_file(
                    file_path=file_path,
                    adapter_type=adapter_type,
                    device_id=device_id,
                    threshold=threshold,
                    model=model,
                    store_results=store_results
                )
                
                # Log success
                logger.info(f"Successfully processed file {file.filename}, found {len(anomalies)} anomalies")
                
                # Clean up file
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                return anomalies
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                
                # Clean up file
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                return None
        
        # Add task to background
        background_tasks.add_task(process_file)
        
        # Return immediate response
        return AnomalyResponse(
            status="processing",
            anomalies_detected=0,
            anomalies=[]
        )
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        
        # Clean up file if it exists
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/status/{job_id}", response_model=AnomalyResponse)
async def get_file_processing_status(job_id: str, current_user: User = Depends(get_current_active_user)):
    """
    Get the status of a file processing job
    
    Parameters:
        job_id: The ID of the job to check
    
    Returns:
        AnomalyResponse with job status and results if available
    """
    # This would typically check a job queue or database for the status
    # For now, we'll return a placeholder response
    return AnomalyResponse(
        status="not_implemented",
        anomalies_detected=0,
        anomalies=[]
    )
