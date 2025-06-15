"""Alerts API Routes

This module provides API endpoints for managing alerts.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field

from utils.logger import get_logger
from utils.database import get_db_connection
from api.auth.utils import get_current_active_user
from api.auth.models import User

# Get logger
logger = get_logger()

# Create router
router = APIRouter(prefix="/alerts", tags=["alerts"])

# Models
class AlertBase(BaseModel):
    """Base alert model"""
    anomaly_id: int
    severity: str
    message: str

class AlertCreate(AlertBase):
    """Alert creation model"""
    pass

class AlertUpdate(BaseModel):
    """Alert update model"""
    acknowledged: Optional[bool] = None
    cleared_at: Optional[datetime] = None

class Alert(AlertBase):
    """Complete alert model"""
    id: int
    raised_at: datetime
    cleared_at: Optional[datetime] = None
    acknowledged: bool
    
    class Config:
        orm_mode = True

# API Routes
@router.get("/", response_model=List[Alert])
async def get_alerts(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    severity: Optional[str] = Query(None, description="Filter by severity (info, warning, critical)"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment status"),
    current_user: User = Depends(get_current_active_user)
):
    """Get alerts with optional filtering"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query with filters
        query = "SELECT * FROM alerts WHERE 1=1"
        params = []
        
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        if acknowledged is not None:
            query += " AND acknowledged = ?"
            params.append(1 if acknowledged else 0)
        
        # Add order and pagination
        query += " ORDER BY raised_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute query
        cursor.execute(query, params)
        alerts = cursor.fetchall()
        
        # Convert to list of dicts
        result = [dict(alert) for alert in alerts]
        conn.close()
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting alerts: {str(e)}")

@router.get("/statistics")
async def get_alert_statistics(
    days: int = Query(7, ge=1, le=30, description="Number of days to include in statistics"),
    current_user: User = Depends(get_current_active_user)
):
    """Get alert statistics for dashboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get counts by severity
        cursor.execute("""
        SELECT severity, COUNT(*) as count 
        FROM alerts 
        WHERE raised_at >= datetime('now', '-' || ? || ' days')
        GROUP BY severity
        """, (days,))
        
        severity_counts = {row['severity']: row['count'] for row in cursor.fetchall()}
        
        # Get counts by acknowledgment status
        cursor.execute("""
        SELECT acknowledged, COUNT(*) as count 
        FROM alerts 
        WHERE raised_at >= datetime('now', '-' || ? || ' days')
        GROUP BY acknowledged
        """, (days,))
        
        ack_counts = {}
        for row in cursor.fetchall():
            key = "acknowledged" if row['acknowledged'] else "unacknowledged"
            ack_counts[key] = row['count']
        
        # Get daily counts
        cursor.execute("""
        SELECT date(raised_at) as day, COUNT(*) as count 
        FROM alerts 
        WHERE raised_at >= datetime('now', '-' || ? || ' days')
        GROUP BY date(raised_at)
        ORDER BY day
        """, (days,))
        
        daily_counts = {row['day']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "by_severity": severity_counts,
            "by_status": ack_counts,
            "daily": daily_counts,
            "total": sum(severity_counts.values())
        }
    
    except Exception as e:
        logger.error(f"Error getting alert statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting alert statistics: {str(e)}")

@router.get("/{alert_id}", response_model=Alert)
async def get_alert(
    alert_id: int = Path(..., description="The ID of the alert to retrieve"),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific alert by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
        alert = cursor.fetchone()
        
        conn.close()
        
        if not alert:
            raise HTTPException(status_code=404, detail=f"Alert with ID {alert_id} not found")
        
        return dict(alert)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting alert: {str(e)}")

@router.patch("/{alert_id}", response_model=Alert)
async def update_alert(
    alert_update: AlertUpdate,
    alert_id: int = Path(..., description="The ID of the alert to update"),
    current_user: User = Depends(get_current_active_user)
):
    """Update an alert (acknowledge or clear)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if alert exists
        cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
        alert = cursor.fetchone()
        
        if not alert:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Alert with ID {alert_id} not found")
        
        # Build update query
        query = "UPDATE alerts SET "
        params = []
        updates = []
        
        if alert_update.acknowledged is not None:
            updates.append("acknowledged = ?")
            params.append(1 if alert_update.acknowledged else 0)
        
        if alert_update.cleared_at is not None:
            updates.append("cleared_at = ?")
            params.append(alert_update.cleared_at.isoformat())
        elif alert_update.acknowledged and alert['cleared_at'] is None:
            # Automatically set cleared_at when acknowledging
            updates.append("cleared_at = ?")
            params.append(datetime.now().isoformat())
        
        if not updates:
            conn.close()
            return dict(alert)
        
        query += ", ".join(updates)
        query += " WHERE id = ?"
        params.append(alert_id)
        
        # Execute update
        cursor.execute(query, params)
        conn.commit()
        
        # Get updated alert
        cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
        updated_alert = cursor.fetchone()
        
        conn.close()
        
        logger.info(f"Alert {alert_id} updated by {current_user.username}")
        return dict(updated_alert)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating alert: {str(e)}")

@router.post("/acknowledge-all")
async def acknowledge_all_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity (info, warning, critical)"),
    current_user: User = Depends(get_current_active_user)
):
    """Acknowledge all alerts, optionally filtered by severity"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query with filters
        query = "UPDATE alerts SET acknowledged = 1, cleared_at = ? WHERE acknowledged = 0"
        params = [datetime.now().isoformat()]
        
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        # Execute update
        cursor.execute(query, params)
        count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"{count} alerts acknowledged by {current_user.username}")
        return {"acknowledged": count}
    
    except Exception as e:
        logger.error(f"Error acknowledging alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error acknowledging alerts: {str(e)}")
