"""Model API Routes

This module provides API endpoints for managing ML models and their settings.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from utils.logger import get_logger
from utils.database import get_db_connection
from ml.anomaly_detector import load_models, get_model_status, retrain_model, set_threshold
from api.auth.utils import get_current_active_user
from api.auth.models import User

# Get logger
logger = get_logger()

# Create router
router = APIRouter(prefix="/model", tags=["model"])

# Models
class ModelSettings(BaseModel):
    """Model settings for updating threshold and model selection"""
    threshold: float = Field(0.7, ge=0.1, le=0.95)
    model: str = Field('both', description="Model to use for detection (isolation_forest, local_outlier_factor, or both)")

class ModelRetrainRequest(BaseModel):
    """Request model for retraining"""
    model: str = Field('both', description="Model to retrain (isolation_forest, local_outlier_factor, or both)")

@router.get("/info")
async def get_model_info(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get model information and current settings"""
    try:
        # Get model status
        model_status = get_model_status()
        
        # Get current threshold from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT value FROM settings WHERE key = 'anomaly_threshold'
        """)
        
        threshold_row = cursor.fetchone()
        threshold = float(threshold_row['value']) if threshold_row else 0.7
        
        # Get last training time
        cursor.execute("""
        SELECT value FROM settings WHERE key = 'last_model_training'
        """)
        
        last_trained_row = cursor.fetchone()
        last_trained = last_trained_row['value'] if last_trained_row else None
        
        # Get current model
        cursor.execute("""
        SELECT value FROM settings WHERE key = 'current_model'
        """)
        
        current_model_row = cursor.fetchone()
        current_model = current_model_row['value'] if current_model_row else 'both'
        
        conn.close()
        
        # Return combined information
        return {
            "threshold": threshold,
            "current_model": current_model,
            "last_trained": last_trained or datetime.now().isoformat(),
            "accuracy": model_status.get('accuracy', 0.0) * 100,
            "status": model_status.get('status', 'idle'),
            "models": model_status.get('models', {})
        }
    
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting model info: {str(e)}")

@router.post("/settings")
async def update_model_settings(
    settings: ModelSettings,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Update model settings"""
    try:
        # Validate model selection
        valid_models = ['isolation_forest', 'local_outlier_factor', 'both']
        if settings.model not in valid_models:
            raise HTTPException(status_code=400, detail=f"Invalid model selection. Must be one of: {', '.join(valid_models)}")
        
        # Update threshold in ML module
        set_threshold(settings.threshold)
        
        # Save settings to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update threshold
        cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value) VALUES ('anomaly_threshold', ?)
        """, (str(settings.threshold),))
        
        # Update current model
        cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value) VALUES ('current_model', ?)
        """, (settings.model,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Model settings updated by {current_user.username}: threshold={settings.threshold}, model={settings.model}")
        
        return {
            "success": True,
            "message": "Settings updated successfully",
            "settings": {
                "threshold": settings.threshold,
                "model": settings.model
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating model settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating model settings: {str(e)}")

@router.post("/retrain")
async def start_model_retraining(
    request: ModelRetrainRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Start model retraining process"""
    try:
        # Validate model selection
        valid_models = ['isolation_forest', 'local_outlier_factor', 'both']
        if request.model not in valid_models:
            raise HTTPException(status_code=400, detail=f"Invalid model selection. Must be one of: {', '.join(valid_models)}")
        
        # Update training status in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value) VALUES ('model_training_status', 'training')
        """)
        
        conn.commit()
        conn.close()
        
        # Start retraining in background
        background_tasks.add_task(retrain_model, request.model)
        
        logger.info(f"Model retraining initiated by {current_user.username}: model={request.model}")
        
        return {
            "success": True,
            "message": f"Retraining of {request.model} model(s) initiated",
            "status": "training"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating model retraining: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initiating model retraining: {str(e)}")
