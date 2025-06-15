"""
Scheduler API

This module provides API endpoints for managing scheduled tasks.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel, Field

from utils.logger import get_logger
from utils.scheduler import (
    initialize_scheduler, 
    schedule_interval_task, 
    schedule_cron_task, 
    remove_task, 
    get_active_tasks
)
from ml.integration import detect_anomalies_from_traffic
from api.dependencies import get_anomaly_detector, validate_threshold
from api.auth import get_current_active_user, check_admin_role
from api.auth.models import User

# Get logger
logger = get_logger()

# Create router
router = APIRouter(prefix="/scheduler", tags=["scheduler"])

# Define Pydantic models
class IntervalTaskRequest(BaseModel):
    """Request model for creating an interval task"""
    task_id: str
    seconds: int = 0
    minutes: int = 0
    hours: int = 0
    days: int = 0
    device_id: Optional[int] = None
    threshold: Optional[float] = None
    model: Optional[str] = "both"
    store_results: bool = True

class CronTaskRequest(BaseModel):
    """Request model for creating a cron task"""
    task_id: str
    cron_expression: str
    device_id: Optional[int] = None
    threshold: Optional[float] = None
    model: Optional[str] = "both"
    store_results: bool = True

class TaskResponse(BaseModel):
    """Response model for task operations"""
    task_id: str
    status: str
    message: str

class TaskInfo(BaseModel):
    """Model for task information"""
    id: str
    name: Optional[str] = None
    next_run_time: Optional[str] = None
    trigger: str

class TaskListResponse(BaseModel):
    """Response model for listing tasks"""
    tasks: Dict[str, TaskInfo]
    count: int

@router.post("/interval", response_model=TaskResponse)
async def create_interval_task(
    request: IntervalTaskRequest,
    background_tasks: BackgroundTasks,
    anomaly_detector = Depends(get_anomaly_detector),
    threshold: float = Depends(validate_threshold),
    current_user: User = Depends(check_admin_role)  # Require admin role
):
    """
    Create a new task that runs at a fixed interval
    
    Parameters:
        request: IntervalTaskRequest containing task parameters
        background_tasks: FastAPI background tasks handler
        anomaly_detector: Anomaly detector instance from dependency
        threshold: Validated threshold from dependency
    
    Returns:
        TaskResponse with task information
    """
    try:
        # Initialize scheduler if needed
        initialize_scheduler()
        
        # Use the threshold from dependency if not provided in request
        if request.threshold is not None:
            threshold = request.threshold
        
        # Define the task function
        async def scheduled_anomaly_detection():
            try:
                # Detect anomalies
                anomalies = detect_anomalies_from_traffic(
                    device_id=request.device_id,
                    limit=100,
                    threshold=threshold,
                    model=request.model
                )
                
                # Store results if requested
                if request.store_results and len(anomalies) > 0:
                    from utils.database import insert_anomalies
                    insert_anomalies(anomalies)
                
                logger.info(f"Scheduled task '{request.task_id}' completed, found {len(anomalies)} anomalies")
            except Exception as e:
                logger.error(f"Error in scheduled task '{request.task_id}': {str(e)}")
        
        # Schedule the task
        job_id = schedule_interval_task(
            task_id=request.task_id,
            func=scheduled_anomaly_detection,
            seconds=request.seconds,
            minutes=request.minutes,
            hours=request.hours,
            days=request.days
        )
        
        return TaskResponse(
            task_id=job_id,
            status="scheduled",
            message=f"Task '{request.task_id}' scheduled successfully"
        )
    
    except Exception as e:
        logger.error(f"Error scheduling task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/cron", response_model=TaskResponse)
async def create_cron_task(
    request: CronTaskRequest,
    background_tasks: BackgroundTasks,
    anomaly_detector = Depends(get_anomaly_detector),
    threshold: float = Depends(validate_threshold),
    current_user: User = Depends(check_admin_role)  # Require admin role
):
    """
    Create a new task that runs on a cron schedule
    
    Parameters:
        request: CronTaskRequest containing task parameters
        background_tasks: FastAPI background tasks handler
        anomaly_detector: Anomaly detector instance from dependency
        threshold: Validated threshold from dependency
    
    Returns:
        TaskResponse with task information
    """
    try:
        # Initialize scheduler if needed
        initialize_scheduler()
        
        # Use the threshold from dependency if not provided in request
        if request.threshold is not None:
            threshold = request.threshold
        
        # Define the task function
        async def scheduled_anomaly_detection():
            try:
                # Detect anomalies
                anomalies = detect_anomalies_from_traffic(
                    device_id=request.device_id,
                    limit=100,
                    threshold=threshold,
                    model=request.model
                )
                
                # Store results if requested
                if request.store_results and len(anomalies) > 0:
                    from utils.database import insert_anomalies
                    insert_anomalies(anomalies)
                
                logger.info(f"Scheduled task '{request.task_id}' completed, found {len(anomalies)} anomalies")
            except Exception as e:
                logger.error(f"Error in scheduled task '{request.task_id}': {str(e)}")
        
        # Schedule the task
        job_id = schedule_cron_task(
            task_id=request.task_id,
            func=scheduled_anomaly_detection,
            cron_expression=request.cron_expression
        )
        
        return TaskResponse(
            task_id=job_id,
            status="scheduled",
            message=f"Task '{request.task_id}' scheduled successfully"
        )
    
    except Exception as e:
        logger.error(f"Error scheduling task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{task_id}", response_model=TaskResponse)
async def delete_task(task_id: str, current_user: User = Depends(check_admin_role)):
    """
    Delete a scheduled task
    
    Parameters:
        task_id: ID of the task to delete
    
    Returns:
        TaskResponse with operation status
    """
    try:
        # Remove the task
        success = remove_task(task_id)
        
        if success:
            return TaskResponse(
                task_id=task_id,
                status="deleted",
                message=f"Task '{task_id}' deleted successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task '{task_id}' not found"
            )
    
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=TaskListResponse)
async def list_tasks(current_user: User = Depends(get_current_active_user)):
    """
    List all scheduled tasks
    
    Returns:
        TaskListResponse with list of tasks
    """
    try:
        # Get active tasks
        tasks = get_active_tasks()
        
        # Convert to response model
        task_infos = {}
        for task_id, task_data in tasks.items():
            task_infos[task_id] = TaskInfo(
                id=task_data["id"],
                name=task_data.get("name"),
                next_run_time=task_data.get("next_run_time"),
                trigger=task_data.get("trigger")
            )
        
        return TaskListResponse(
            tasks=task_infos,
            count=len(task_infos)
        )
    
    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
