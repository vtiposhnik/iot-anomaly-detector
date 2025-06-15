"""Statistics API Routes

This module provides API endpoints for retrieving statistics for the dashboard.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query

from utils.logger import get_logger
from utils.database import get_db_connection, get_anomaly_statistics
from api.auth.utils import get_current_active_user
from api.auth.models import User

# Get logger
logger = get_logger()

# Create router
router = APIRouter(prefix="/statistics", tags=["statistics"])

@router.get("/dashboard")
async def get_dashboard_statistics(
    days: int = Query(1, ge=1, le=30, description="Number of days to include in statistics"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get dashboard statistics for KPI cards
    
    Returns statistics about traffic, devices, and anomalies for dashboard visualization
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current timestamp
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0).isoformat()
        
        # Get anomalies today
        cursor.execute("""
        SELECT COUNT(*) as count 
        FROM anomalies 
        WHERE detected_at >= ?
        """, (today_start,))
        
        anomalies_today = cursor.fetchone()['count']
        
        # Get devices online (active in the last 24 hours)
        cursor.execute("""
        SELECT COUNT(*) as count 
        FROM devices 
        WHERE last_seen >= datetime('now', '-1 day')
        """)
        
        devices_online = cursor.fetchone()['count']
        
        # Get total traffic in the last 24 hours (in MB)
        cursor.execute("""
        SELECT SUM(orig_bytes + resp_bytes) / 1048576.0 as total_mb
        FROM traffic 
        WHERE timestamp >= datetime('now', '-1 day')
        """)
        
        result = cursor.fetchone()
        total_traffic_mb = round(result['total_mb'] if result['total_mb'] else 0, 2)
        
        # Calculate packets per second (average over last hour)
        cursor.execute("""
        SELECT COUNT(*) as packet_count
        FROM traffic 
        WHERE timestamp >= datetime('now', '-1 hour')
        """)
        
        packet_count = cursor.fetchone()['packet_count']
        packets_per_second = round(packet_count / 3600, 2)  # Average over 1 hour
        
        # Get model accuracy (if available)
        cursor.execute("""
        SELECT AVG(score) as avg_score
        FROM anomalies 
        WHERE is_genuine = 1 AND detected_at >= datetime('now', '-7 day')
        """)
        
        result = cursor.fetchone()
        detection_accuracy = round(result['avg_score'] * 100 if result['avg_score'] else 0, 1)
        
        # Get anomaly statistics
        anomaly_stats = get_anomaly_statistics(days)
        
        conn.close()
        
        # Return combined statistics
        return {
            "anomalies_today": anomalies_today,
            "devices_online": devices_online,
            "total_traffic_mb": total_traffic_mb,
            "packets_per_second": packets_per_second,
            "detection_accuracy": detection_accuracy,
            "anomaly_stats": anomaly_stats
        }
    
    except Exception as e:
        logger.error(f"Error getting dashboard statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting dashboard statistics: {str(e)}")

@router.get("/traffic")
async def get_traffic_statistics(
    days: int = Query(7, ge=1, le=30, description="Number of days to include in statistics"),
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get traffic statistics
    
    Returns statistics about network traffic for visualization
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query parameters
        params = [days]
        device_filter = ""
        
        if device_id is not None:
            device_filter = "AND device_id = ?"
            params.append(device_id)
        
        # Get hourly traffic volume
        cursor.execute(f"""
        SELECT 
            strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
            SUM(orig_bytes + resp_bytes) / 1048576.0 as volume_mb,
            COUNT(*) as packet_count
        FROM traffic 
        WHERE timestamp >= datetime('now', '-' || ? || ' days') {device_filter}
        GROUP BY strftime('%Y-%m-%d %H:00:00', timestamp)
        ORDER BY hour
        """, params)
        
        hourly_traffic = {}
        for row in cursor.fetchall():
            hourly_traffic[row['hour']] = {
                'volume_mb': round(row['volume_mb'], 2),
                'packet_count': row['packet_count']
            }
        
        # Get protocol distribution
        cursor.execute(f"""
        SELECT 
            protocol,
            COUNT(*) as count,
            SUM(orig_bytes + resp_bytes) / 1048576.0 as volume_mb
        FROM traffic 
        WHERE timestamp >= datetime('now', '-' || ? || ' days') {device_filter}
        GROUP BY protocol
        ORDER BY count DESC
        """, params)
        
        protocol_distribution = {}
        for row in cursor.fetchall():
            protocol = row['protocol'] if row['protocol'] else 'unknown'
            protocol_distribution[protocol] = {
                'count': row['count'],
                'volume_mb': round(row['volume_mb'], 2)
            }
        
        conn.close()
        
        return {
            "hourly_traffic": hourly_traffic,
            "protocol_distribution": protocol_distribution
        }
    
    except Exception as e:
        logger.error(f"Error getting traffic statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting traffic statistics: {str(e)}")
