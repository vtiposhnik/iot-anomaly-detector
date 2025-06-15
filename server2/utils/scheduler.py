"""
Background Task Scheduler

This module provides functionality for scheduling periodic background tasks
using FastAPI's background tasks and APScheduler.
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, Callable, List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore

from utils.logger import get_logger
from utils.config import get_config

# Get logger
logger = get_logger()

# Create scheduler
scheduler = AsyncIOScheduler(
    jobstores={"default": MemoryJobStore()},
    timezone="UTC"
)

# Store for active jobs
active_jobs: Dict[str, str] = {}

def initialize_scheduler():
    """Initialize the scheduler and start it"""
    if not scheduler.running:
        scheduler.start()
        logger.info("Background task scheduler started")

def shutdown_scheduler():
    """Shutdown the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background task scheduler shutdown")

def schedule_interval_task(
    task_id: str,
    func: Callable,
    seconds: int = 0,
    minutes: int = 0,
    hours: int = 0,
    days: int = 0,
    start_date: Optional[datetime] = None,
    args: Optional[List] = None,
    kwargs: Optional[Dict[str, Any]] = None
) -> str:
    """
    Schedule a task to run at a fixed interval
    
    Args:
        task_id: Unique identifier for the task
        func: Function to execute
        seconds: Number of seconds between executions
        minutes: Number of minutes between executions
        hours: Number of hours between executions
        days: Number of days between executions
        start_date: When to start the task
        args: Positional arguments to pass to the function
        kwargs: Keyword arguments to pass to the function
        
    Returns:
        Job ID
    """
    # Create trigger
    trigger = IntervalTrigger(
        seconds=seconds,
        minutes=minutes,
        hours=hours,
        days=days,
        start_date=start_date
    )
    
    # Add job
    job = scheduler.add_job(
        func=func,
        trigger=trigger,
        args=args or [],
        kwargs=kwargs or {},
        id=task_id,
        replace_existing=True
    )
    
    # Store job ID
    active_jobs[task_id] = job.id
    
    logger.info(f"Scheduled interval task '{task_id}' with ID {job.id}")
    
    return job.id

def schedule_cron_task(
    task_id: str,
    func: Callable,
    cron_expression: str,
    args: Optional[List] = None,
    kwargs: Optional[Dict[str, Any]] = None
) -> str:
    """
    Schedule a task to run on a cron schedule
    
    Args:
        task_id: Unique identifier for the task
        func: Function to execute
        cron_expression: Cron expression (e.g. "0 0 * * *" for daily at midnight)
        args: Positional arguments to pass to the function
        kwargs: Keyword arguments to pass to the function
        
    Returns:
        Job ID
    """
    # Create trigger
    trigger = CronTrigger.from_crontab(cron_expression)
    
    # Add job
    job = scheduler.add_job(
        func=func,
        trigger=trigger,
        args=args or [],
        kwargs=kwargs or {},
        id=task_id,
        replace_existing=True
    )
    
    # Store job ID
    active_jobs[task_id] = job.id
    
    logger.info(f"Scheduled cron task '{task_id}' with ID {job.id}")
    
    return job.id

def remove_task(task_id: str) -> bool:
    """
    Remove a scheduled task
    
    Args:
        task_id: ID of the task to remove
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Remove job
        scheduler.remove_job(task_id)
        
        # Remove from active jobs
        if task_id in active_jobs:
            del active_jobs[task_id]
        
        logger.info(f"Removed task '{task_id}'")
        
        return True
    except Exception as e:
        logger.error(f"Error removing task '{task_id}': {str(e)}")
        return False

def get_active_tasks() -> Dict[str, Any]:
    """
    Get a list of active tasks
    
    Returns:
        Dictionary of active tasks
    """
    tasks = {}
    
    for job_id in active_jobs.values():
        job = scheduler.get_job(job_id)
        
        if job:
            tasks[job.id] = {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
    
    return tasks
