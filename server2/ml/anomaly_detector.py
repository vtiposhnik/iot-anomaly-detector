"""
Anomaly Detection Module

This module provides functions for detecting anomalies in IoT network traffic data.
It uses scikit-learn's Isolation Forest and Local Outlier Factor algorithms.
"""
import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from .dataset_adapter import extract_features_from_traffic, normalize_features
from utils.logger import get_logger
from utils.database import get_traffic

# Get logger
logger = get_logger()

# Constants
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
ISO_FOREST_MODEL_PATH = os.path.join(MODELS_DIR, 'isolation_forest.pkl')
LOF_MODEL_PATH = os.path.join(MODELS_DIR, 'local_outlier_factor.pkl')
SCALER_PATH = os.path.join(MODELS_DIR, 'scaler.pkl')

# Ensure models directory exists
os.makedirs(MODELS_DIR, exist_ok=True)

# Global model instances
isolation_forest_model = None
lof_model = None
scaler = None

# Model status tracking
model_status = {
    'trained': False,
    'last_training_time': None,
    'isolation_forest': {'trained': False},
    'lof': {'trained': False}
}

def load_models():
    """Load trained models from disk or train new ones if they don't exist."""
    global isolation_forest_model, lof_model, scaler, model_status

    try:
        # Load existing models if present
        if os.path.exists(ISO_FOREST_MODEL_PATH):
            logger.info(f"Loading Isolation Forest model from {ISO_FOREST_MODEL_PATH}")
            isolation_forest_model = joblib.load(ISO_FOREST_MODEL_PATH)
            model_status['isolation_forest']['trained'] = True
        else:
            logger.warning(f"Isolation Forest model not found at {ISO_FOREST_MODEL_PATH}")
            logger.info("Training new Isolation Forest model...")

            traffic_data = get_traffic(limit=10000)
            if not traffic_data:
                logger.error("No traffic data available for training")
                return False

            traffic_df = pd.DataFrame(traffic_data)
            feature_df = extract_features_from_traffic(traffic_df)
            X, scaler_obj, _ = normalize_features(feature_df, training=True)

            joblib.dump(scaler_obj, SCALER_PATH)
            scaler = scaler_obj

            isolation_forest_model = train_isolation_forest(X)
            lof_model = train_lof(X)

            if not isolation_forest_model or not lof_model:
                logger.error("Failed to train models")
                return False

            model_status['isolation_forest']['trained'] = True
            model_status['lof']['trained'] = True

        if os.path.exists(LOF_MODEL_PATH):
            logger.info(f"Loading LOF model from {LOF_MODEL_PATH}")
            lof_model = joblib.load(LOF_MODEL_PATH)
            model_status['lof']['trained'] = True

        if os.path.exists(SCALER_PATH):
            logger.info(f"Loading scaler from {SCALER_PATH}")
            scaler = joblib.load(SCALER_PATH)

        model_status['trained'] = model_status['isolation_forest']['trained'] or model_status['lof']['trained']
        model_status['last_training_time'] = datetime.now().isoformat()

        logger.info("Models loaded successfully")
        return True

    except Exception as e:
        logger.error(f"Error loading models: {str(e)}")
        return False

def train_isolation_forest(X_train, contamination=0.1):
    """
    Train an Isolation Forest model for anomaly detection
    
    Args:
        X_train: Training data
        contamination: Expected proportion of anomalies
    
    Returns:
        Trained model
    """
    try:
        # Create and train the model
        model = IsolationForest(
            n_estimators=100,
            max_samples='auto',
            contamination=contamination,
            random_state=42
        )
        
        model.fit(X_train)
        
        # Save the model
        os.makedirs(os.path.dirname(ISO_FOREST_MODEL_PATH), exist_ok=True)
        joblib.dump(model, ISO_FOREST_MODEL_PATH)
        
        logger.info(f"Isolation Forest model trained and saved to {ISO_FOREST_MODEL_PATH}")
        
        return model
    
    except Exception as e:
        logger.error(f"Error training Isolation Forest model: {str(e)}")
        return None

def train_lof(X_train, contamination=0.1):
    """
    Train a Local Outlier Factor model for anomaly detection
    
    Args:
        X_train: Training data
        contamination: Expected proportion of anomalies
    
    Returns:
        Trained model
    """
    try:
        # Create and train the model
        model = LocalOutlierFactor(
            n_neighbors=20,
            contamination=contamination,
            novelty=True  # Allow prediction on new data
        )
        
        model.fit(X_train)
        
        # Save the model
        os.makedirs(os.path.dirname(LOF_MODEL_PATH), exist_ok=True)
        joblib.dump(model, LOF_MODEL_PATH)
        
        logger.info(f"LOF model trained and saved to {LOF_MODEL_PATH}")
        
        return model
    
    except Exception as e:
        logger.error(f"Error training LOF model: {str(e)}")
        return None

def detect_anomalies(data):
    """
    Detect anomalies in the provided data
    
    Args:
        data: Dictionary or DataFrame containing traffic data
    
    Returns:
        List of detected anomalies
    """
    global isolation_forest_model, lof_model, scaler, model_status
    
    try:
        # Ensure models are loaded
        if not model_status['trained']:
            if not load_models():
                logger.error("Failed to load models for anomaly detection")
                return []
        
        # Convert data to DataFrame if it's a dictionary
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = pd.DataFrame(data)
        
        # Extract features
        feature_df = extract_features_from_traffic(df)
        
        if feature_df.empty:
            logger.warning("No features could be extracted from the data")
            return []
        
        # Normalize features using loaded scaler
        X = scaler.transform(feature_df)
        feature_names = feature_df.columns.tolist()
        
        # Predict anomalies
        anomalies = []
        
        # Use Isolation Forest if available
        if model_status['isolation_forest']['trained']:
            iso_forest_pred = isolation_forest_model.predict(X)
            iso_forest_score = isolation_forest_model.decision_function(X)
        else:
            iso_forest_pred = np.ones(len(X))  # Default to normal
            iso_forest_score = np.zeros(len(X))
        
        # Use LOF if available
        if model_status['lof']['trained']:
            lof_pred = lof_model.predict(X)
            lof_score = lof_model.decision_function(X)
        else:
            lof_pred = np.ones(len(X))  # Default to normal
            lof_score = np.zeros(len(X))
        
        # Combine results
        for i in range(len(X)):
            anomaly_types = []
            
            if iso_forest_pred[i] == -1:
                anomaly_types.append('Isolation Forest')
            
            if lof_pred[i] == -1:
                anomaly_types.append('Local Outlier Factor')
            
            if anomaly_types:
                # Calculate confidence score (negative of the average of normalized scores)
                confidence = -0.5 * (iso_forest_score[i] + lof_score[i])
                
                # Create anomaly record
                anomaly = {
                    'timestamp': df.iloc[i].get('timestamp', datetime.now().isoformat()),
                    'device_id': df.iloc[i].get('device_id', 'unknown'),
                    'anomaly_type': anomaly_types,
                    'confidence': float(confidence),
                    'features': {name: float(feature_df.iloc[i][name]) if isinstance(feature_df.iloc[i][name], (int, float)) else feature_df.iloc[i][name] for name in feature_names if name in feature_df.columns}
                }
                
                anomalies.append(anomaly)
        
        logger.info(f"Detected {len(anomalies)} anomalies in {len(X)} records")
        return anomalies
    
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")
        return []

def get_model_status():
    """
    Get the current status of the anomaly detection models
    
    Returns:
        Dictionary with model status information
    """
    global model_status
    return model_status


def get_model_status():
    """Get the current status of the anomaly detection models"""
    return model_status

def set_threshold(threshold: float) -> None:
    """
    Set the anomaly detection threshold
    
    Args:
        threshold: New threshold value (between 0.1 and 0.95)
    """
    global model_status
    
    # Validate threshold
    if threshold < 0.1 or threshold > 0.95:
        logger.error(f"Invalid threshold value: {threshold}. Must be between 0.1 and 0.95")
        return
    
    # Update threshold in model status
    model_status['threshold'] = threshold
    logger.info(f"Anomaly detection threshold updated to {threshold}")


def retrain_model(model_type: str = 'both') -> None:
    """
    Retrain the specified anomaly detection model(s)
    
    Args:
        model_type: Type of model to retrain ('isolation_forest', 'local_outlier_factor', or 'both')
    
    Returns:
        None
    """
    global isolation_forest_model, lof_model, scaler, model_status
    
    try:
        # Update model status
        model_status['status'] = 'training'
        model_status['last_training_time'] = datetime.now().isoformat()
        
        # Get training data
        logger.info(f"Retrieving training data for model retraining: {model_type}")
        
        # Get traffic data from database
        traffic_data = get_traffic(limit=10000)  # Get a large sample for training
        
        if not traffic_data or len(traffic_data) < 100:
            logger.error("Insufficient data for model training. Need at least 100 samples.")
            model_status['status'] = 'error'
            model_status['error'] = "Insufficient data for model training"
            return
        
        # Extract features for training
        features = []
        for item in traffic_data:
            try:
                extracted = extract_features_from_traffic(item)
                if extracted is not None:
                    features.append(extracted)
            except Exception as e:
                logger.error(f"Error extracting features: {str(e)}")
        
        if len(features) < 100:
            logger.error("Insufficient valid features for model training")
            model_status['status'] = 'error'
            model_status['error'] = "Insufficient valid features for model training"
            return
        
        # Convert to DataFrame
        X_train = pd.DataFrame(features)
        
        # Fit scaler on training data
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        
        # Save scaler
        joblib.dump(scaler, SCALER_PATH)
        logger.info(f"Saved scaler to {SCALER_PATH}")
        
        # Train models based on selection
        if model_type in ['isolation_forest', 'both']:
            # Train Isolation Forest
            isolation_forest_model = train_isolation_forest(X_train_scaled)
            joblib.dump(isolation_forest_model, ISO_FOREST_MODEL_PATH)
            logger.info(f"Trained and saved Isolation Forest model to {ISO_FOREST_MODEL_PATH}")
            model_status['isolation_forest']['trained'] = True
            model_status['isolation_forest']['last_trained'] = datetime.now().isoformat()
        
        if model_type in ['local_outlier_factor', 'both']:
            # Train LOF
            lof_model = train_lof(X_train_scaled)
            joblib.dump(lof_model, LOF_MODEL_PATH)
            logger.info(f"Trained and saved LOF model to {LOF_MODEL_PATH}")
            model_status['lof']['trained'] = True
            model_status['lof']['last_trained'] = datetime.now().isoformat()
        
        # Update model status
        model_status['trained'] = True
        model_status['status'] = 'idle'
        model_status['accuracy'] = 0.85  # Placeholder for actual accuracy metric
        
        logger.info(f"Model retraining completed successfully for {model_type}")
        
    except Exception as e:
        logger.error(f"Error during model retraining: {str(e)}")
        model_status['status'] = 'error'
        model_status['error'] = str(e)

# Initialize by loading models if they exist
load_models()
