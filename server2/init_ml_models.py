"""
Initialize ML Models

This script initializes the machine learning models for anomaly detection.
"""
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
from utils.logger import setup_logger
from utils.database import get_traffic
from ml.dataset_adapter import extract_features_from_traffic, normalize_features

# Setup logger
logger = setup_logger()

# Constants
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')
SCALER_PATH = os.path.join(MODELS_DIR, 'scaler.pkl')

def create_scaler():
    """Create and save a scaler for feature normalization"""
    # Get traffic data
    traffic_data = get_traffic(limit=10000)
    
    if not traffic_data:
        logger.error("No traffic data available")
        return False
    
    # Convert to DataFrame
    traffic_df = pd.DataFrame(traffic_data)
    
    # Extract features
    feature_df = extract_features_from_traffic(traffic_df)
    
    if feature_df.empty:
        logger.error("Failed to extract features")
        return False
    
    # Create and fit scaler
    scaler = StandardScaler()
    scaler.fit(feature_df)
    
    # Save scaler
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(scaler, SCALER_PATH)
    
    logger.info(f"Scaler created and saved to {SCALER_PATH}")
    return True

if __name__ == "__main__":
    logger.info("Initializing ML models...")
    
    # Create scaler
    if create_scaler():
        logger.info("Scaler initialized successfully")
    else:
        logger.error("Failed to initialize scaler")
    
    logger.info("ML model initialization complete")
