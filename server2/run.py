"""
IoT Anomaly Detection System - Server Runner

This script starts the FastAPI application using Uvicorn.
"""
import uvicorn
import os
from utils.logger import setup_logger

# Setup logging
logger = setup_logger()

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 5000))
    
    # Log startup
    logger.info(f"Starting IoT Anomaly Detection API on port {port}")
    
    # Run server
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        log_level="info"
    )
