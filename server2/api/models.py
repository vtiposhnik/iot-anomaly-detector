"""
API Models

This module contains Pydantic models for request/response validation in the FastAPI application.
"""
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
import re

# Base Models
class DeviceBase(BaseModel):
    """Base model for device information"""
    device_id: int
    ip_address: str
    
    @validator('ip_address')
    def validate_ip(cls, v):
        """Validate IP address format"""
        ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        if not ip_pattern.match(v):
            raise ValueError('Invalid IP address format')
        return v

# Device Models
class DeviceCreate(DeviceBase):
    """Model for creating a new device"""
    type_id: int
    name: Optional[str] = None
    location: Optional[str] = None

class DeviceUpdate(BaseModel):
    """Model for updating an existing device"""
    ip_address: Optional[str] = None
    type_id: Optional[int] = None
    status: Optional[bool] = None
    name: Optional[str] = None
    location: Optional[str] = None

class Device(DeviceBase):
    """Complete device model with all fields"""
    type_id: int
    status: bool
    last_seen: datetime
    name: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    
    class Config:
        orm_mode = True

# Traffic Models
class TrafficBase(BaseModel):
    """Base model for network traffic data"""
    device_id: int
    source_ip: str
    source_port: int
    dest_ip: str
    dest_port: int
    protocol: str
    
    @validator('source_port', 'dest_port')
    def validate_port(cls, v):
        """Validate port number range"""
        if not 0 <= v <= 65535:
            raise ValueError('Port number must be between 0 and 65535')
        return v

class TrafficCreate(TrafficBase):
    """Model for creating new traffic records"""
    timestamp: datetime = Field(default_factory=datetime.now)
    service: Optional[str] = None
    duration: float = 0.0
    orig_bytes: int = 0
    resp_bytes: int = 0
    conn_state: Optional[str] = None
    packet_size: Optional[int] = None

class TrafficData(TrafficBase):
    """Complete traffic data model with all fields"""
    log_id: int
    timestamp: datetime
    service: Optional[str] = None
    duration: float
    orig_bytes: int
    resp_bytes: int
    conn_state: Optional[str] = None
    packet_size: Optional[int] = None
    
    class Config:
        orm_mode = True

# Anomaly Models
class AnomalyBase(BaseModel):
    """Base model for anomaly information"""
    log_id: int
    device_id: int
    score: float = Field(..., ge=0.0, le=1.0)
    
    @validator('score')
    def validate_score(cls, v):
        """Validate anomaly score range"""
        if not 0 <= v <= 1:
            raise ValueError('Anomaly score must be between 0 and 1')
        return v

class AnomalyCreate(AnomalyBase):
    """Model for creating new anomaly records"""
    type_id: int
    is_genuine: bool = True
    model_used: str
    detected_at: datetime = Field(default_factory=datetime.now)

class Anomaly(AnomalyBase):
    """Complete anomaly model with all fields"""
    anomaly_id: int
    type_id: int
    is_genuine: bool
    model_used: str
    detected_at: datetime
    
    class Config:
        orm_mode = True

class AnomalyItem(BaseModel):
    """Simplified anomaly item for API responses"""
    timestamp: str
    device_id: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    score: float
    model_used: str
    is_genuine: bool = True

# Request/Response Models
class AnomalyDetectionRequest(BaseModel):
    """Request model for anomaly detection"""
    device_id: Optional[int] = None
    limit: int = Field(default=100, ge=1, le=1000)
    threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)
    model: Optional[str] = Field(default="both", description="Model to use: isolation_forest, lof, or both")
    store_results: bool = True

class AnomalyResponse(BaseModel):
    """Response model for anomaly detection"""
    status: str
    anomalies_detected: int
    anomalies: List[AnomalyItem]

class ModelStatus(BaseModel):
    """Model for ML model status"""
    isolation_forest: bool
    lof: bool

class ConfigStatus(BaseModel):
    """Model for configuration status"""
    default_threshold: float
    default_model: str

class StatusResponse(BaseModel):
    """Response model for system status"""
    status: str
    models: ModelStatus
    config: ConfigStatus

class ErrorResponse(BaseModel):
    """Response model for error messages"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
