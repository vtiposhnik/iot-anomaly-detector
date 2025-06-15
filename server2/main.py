"""
IoT Anomaly Detection System - FastAPI Application

This is the main entry point for the FastAPI-based backend of the IoT monitoring application.
"""
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
import pandas as pd

# Import our custom modules
from utils.logger import setup_logger, get_logger
from utils.database import init_db, import_csv_to_db, get_devices, get_traffic, get_anomalies
from ml.anomaly_detector import load_models, detect_anomalies, get_model_status
from api.generic_detect import router as generic_router
from api.file_upload import router as file_router
from api.scheduler import router as scheduler_router
from api.auth import router as auth_router
from api.auth.middleware import AuthMiddleware
from api.models import ErrorResponse
from api.alerts_routes import router as alerts_router
from api.statistics_routes import router as statistics_router
from api.model_routes import router as model_router

# Setup logging
logger = setup_logger()

# Initialize FastAPI application
app = FastAPI(
    title="IoT Anomaly Detection API",
    description="API for detecting anomalies in IoT network traffic",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add authentication middleware
public_endpoints = [
    "/",                 # Root endpoint
    "/api/v1/auth/token",  # Login endpoint
    "/docs",              # Swagger UI
    "/redoc",             # ReDoc
    "/openapi.json"       # OpenAPI schema
]
app.add_middleware(AuthMiddleware, public_endpoints=public_endpoints)

# Add custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(generic_router, prefix="/api/v1")
app.include_router(file_router, prefix="/api/v1")
app.include_router(scheduler_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(statistics_router, prefix="/api/v1")
app.include_router(model_router, prefix="/api/v1")

# Define Pydantic models for request/response validation
class Device(BaseModel):
    device_id: int
    ip_address: str
    type_id: int
    status: bool
    last_seen: datetime
    name: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None

class TrafficData(BaseModel):
    log_id: int
    device_id: int
    timestamp: datetime
    source_ip: str
    source_port: int
    dest_ip: str
    dest_port: int
    protocol: str
    service: Optional[str] = None
    duration: float
    orig_bytes: int
    resp_bytes: int
    conn_state: Optional[str] = None
    packet_size: Optional[int] = None

class Anomaly(BaseModel):
    anomaly_id: int
    log_id: int
    device_id: int
    type_id: int
    score: float
    is_genuine: bool
    model_used: str
    detected_at: datetime

class Alert(BaseModel):
    id: int
    anomaly_id: int
    raised_at: datetime
    cleared_at: Optional[datetime] = None
    severity: str
    message: str
    acknowledged: bool = False

class AnomalyRequest(BaseModel):
    device_id: Optional[int] = None
    data: Optional[List[Dict[str, Any]]] = None
    model: Optional[str] = "both"
    threshold: Optional[float] = 0.7

class StatusResponse(BaseModel):
    status: str
    model: Dict[str, Any]

# Default route
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "IoT Anomaly Detection API",
        "version": "1.0.0"
    }

# API v1 routes
@app.get("/api/v1/status", response_model=StatusResponse)
async def status():
    """Return the status of the API and ML models"""
    return {
        "status": "online",
        "model": get_model_status()
    }

@app.get("/api/v1/devices", response_model=List[Device])
async def get_all_devices(limit: int = Query(100, ge=1, le=1000)):
    """Return a list of all monitored devices"""
    devices = get_devices(limit=limit)
    
    # Enhance device data with more readable information
    for device in devices:
        device['name'] = f"Device {device['device_id']}"
        device['type'] = "IoT Sensor"
        device['location'] = "Network Edge"
    
    return devices

@app.get("/api/v1/data")
async def get_data(
    device_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Return sensor data, optionally filtered by device ID"""
    traffic_data = get_traffic(limit=limit)
    
    # Filter by device ID if provided
    if device_id is not None:
        traffic_data = [item for item in traffic_data if item['device_id'] == device_id]
    
    return traffic_data

@app.get("/api/v1/anomalies", response_model=List[Dict[str, Any]])
async def get_all_anomalies(
    device_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Return detected anomalies, optionally filtered by device ID"""
    anomalies = get_anomalies(limit=limit)
    
    # Filter by device ID if provided
    if device_id is not None:
        anomalies = [item for item in anomalies if item['device_id'] == device_id]
    
    return anomalies

@app.post("/api/v1/detect")
async def detect(request: AnomalyRequest, background_tasks: BackgroundTasks):
    """Process new data and detect anomalies"""
    try:
        # Get parameters
        device_id = request.device_id
        data = request.data
        model = request.model
        threshold = request.threshold
        
        # If data is provided, use it directly
        if data:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Detect anomalies (FastAPI will handle this in a non-blocking way)
            result = detect_anomalies(df, device_id=device_id, threshold=threshold, model=model)
            
            return {
                "status": "success",
                "anomalies_detected": len(result),
                "anomalies": result
            }
        
        # Otherwise, use data from the database
        else:
            # Get traffic data
            traffic_data = get_traffic(limit=100)
            
            # Filter by device ID if provided
            if device_id is not None:
                traffic_data = [item for item in traffic_data if item['device_id'] == device_id]
            
            # Convert to DataFrame
            df = pd.DataFrame(traffic_data)
            
            # Detect anomalies
            result = detect_anomalies(df, device_id=device_id, threshold=threshold, model=model)
            
            return {
                "status": "success",
                "anomalies_detected": len(result),
                "anomalies": result
            }
    
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def initialize_system():
    """Initialize the system by setting up the database and loading models"""
    try:
        # Initialize database
        logger.info("Initializing database...")
        if not init_db():
            logger.error("Failed to initialize database")
            return False
        
        # Import data to database
        logger.info("Importing data to database...")
        if not import_csv_to_db():
            logger.warning("Failed to import data to database")
        
        # Load ML models
        logger.info("Loading ML models...")
        if not load_models():
            logger.warning("Failed to load ML models")
        
        logger.info("System initialization completed")
        return True
    
    except Exception as e:
        logger.error(f"Error initializing system: {str(e)}")
        return False

# Initialize system on startup
@app.on_event("startup")
async def startup_event():
    initialize_system()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
