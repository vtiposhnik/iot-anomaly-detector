"""
Generic Anomaly Detector

This module provides a generic anomaly detector that can work with any network traffic data
that has been normalized by our adapters and processed by our feature extractor.
"""
import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from utils.logger import get_logger
from .feature_extractor import extract_features

# Get logger
logger = get_logger()

# Constants
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
ISO_FOREST_MODEL_PATH = os.path.join(MODELS_DIR, 'isolation_forest.pkl')
LOF_MODEL_PATH = os.path.join(MODELS_DIR, 'local_outlier_factor.pkl')

# Ensure models directory exists
os.makedirs(MODELS_DIR, exist_ok=True)

class GenericAnomalyDetector:
    """
    Generic anomaly detector that can work with any network traffic data.
    
    This class provides methods for training and using anomaly detection models
    on network traffic data from any source.
    """
    
    def __init__(self):
        """Initialize the anomaly detector"""
        self.isolation_forest = None
        self.lof = None
        self.feature_names = []
        
        # Try to load existing models
        self._load_models()
    
    def _load_models(self):
        """Load existing models if available"""
        try:
            if os.path.exists(ISO_FOREST_MODEL_PATH):
                self.isolation_forest = joblib.load(ISO_FOREST_MODEL_PATH)
                logger.info(f"Loaded Isolation Forest model from {ISO_FOREST_MODEL_PATH}")
            
            if os.path.exists(LOF_MODEL_PATH):
                self.lof = joblib.load(LOF_MODEL_PATH)
                logger.info(f"Loaded Local Outlier Factor model from {LOF_MODEL_PATH}")
            
            return self.isolation_forest is not None and self.lof is not None
        
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            return False
    
    def train(self, normalized_data, contamination=0.1):
        """
        Train anomaly detection models on normalized data
        
        Args:
            normalized_data: Pandas DataFrame with normalized network traffic data
            contamination: Expected proportion of anomalies in the data
            
        Returns:
            Boolean indicating if training was successful
        """
        try:
            logger.info(f"Training anomaly detection models on {len(normalized_data)} samples")
            
            # Extract features
            X_train, feature_names = extract_features(normalized_data, advanced=True, normalize=True, training=True)
            self.feature_names = feature_names
            
            logger.info(f"Extracted {len(feature_names)} features: {feature_names}")
            
            # Train Isolation Forest
            self.isolation_forest = IsolationForest(
                n_estimators=100,
                max_samples='auto',
                contamination=contamination,
                random_state=42
            )
            
            self.isolation_forest.fit(X_train)
            
            # Train Local Outlier Factor
            self.lof = LocalOutlierFactor(
                n_neighbors=20,
                contamination=contamination,
                novelty=True
            )
            
            self.lof.fit(X_train)
            
            # Save models
            joblib.dump(self.isolation_forest, ISO_FOREST_MODEL_PATH)
            joblib.dump(self.lof, LOF_MODEL_PATH)
            
            logger.info("Models trained and saved successfully")
            
            return True
        
        except Exception as e:
            logger.error(f"Error training models: {str(e)}")
            return False
    
    def detect_anomalies(self, normalized_data, threshold=None, model='both'):
        """
        Detect anomalies in normalized data
        
        Args:
            normalized_data: Pandas DataFrame with normalized network traffic data
            threshold: Score threshold for anomaly detection (if None, use model default)
            model: Which model to use ('isolation_forest', 'lof', or 'both')
            
        Returns:
            DataFrame with original data and anomaly scores/predictions
        """
        try:
            # Check if models are loaded
            if not self._load_models():
                raise ValueError("Models not loaded. Train models first.")
            
            # Extract features
            X, _ = extract_features(normalized_data, advanced=True, normalize=True, training=False)
            
            # Create result DataFrame
            result = normalized_data.copy()
            
            # Detect anomalies using Isolation Forest
            if model in ['isolation_forest', 'both']:
                # Get anomaly scores (-1 for anomalies, 1 for normal)
                if_scores = self.isolation_forest.decision_function(X)
                # Convert to range [0, 1] where higher values are more anomalous
                result['if_score'] = 1 - ((if_scores + 1) / 2)
                result['if_anomaly'] = self.isolation_forest.predict(X) == -1
            
            # Detect anomalies using Local Outlier Factor
            if model in ['lof', 'both']:
                # Get anomaly scores (negative values are more anomalous)
                lof_scores = self.lof.decision_function(X)
                # Convert to range [0, 1] where higher values are more anomalous
                result['lof_score'] = 1 - ((lof_scores - lof_scores.min()) / (lof_scores.max() - lof_scores.min()))
                result['lof_anomaly'] = lof_scores < 0
            
            # Combine scores if using both models
            if model == 'both':
                result['combined_score'] = (result['if_score'] + result['lof_score']) / 2
                
                if threshold is not None:
                    result['is_anomaly'] = result['combined_score'] > threshold
                else:
                    result['is_anomaly'] = result['if_anomaly'] | result['lof_anomaly']
            elif model == 'isolation_forest':
                if threshold is not None:
                    result['is_anomaly'] = result['if_score'] > threshold
                else:
                    result['is_anomaly'] = result['if_anomaly']
            elif model == 'lof':
                if threshold is not None:
                    result['is_anomaly'] = result['lof_score'] > threshold
                else:
                    result['is_anomaly'] = result['lof_anomaly']
            
            return result
        
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            raise

# Create a singleton instance
anomaly_detector = GenericAnomalyDetector()

def train_models(normalized_data, contamination=0.1):
    """
    Train anomaly detection models on normalized data
    
    Args:
        normalized_data: Pandas DataFrame with normalized network traffic data
        contamination: Expected proportion of anomalies in the data
        
    Returns:
        Boolean indicating if training was successful
    """
    return anomaly_detector.train(normalized_data, contamination)

def detect_anomalies(normalized_data, threshold=None, model='both'):
    """
    Detect anomalies in normalized data
    
    Args:
        normalized_data: Pandas DataFrame with normalized network traffic data
        threshold: Score threshold for anomaly detection (if None, use model default)
        model: Which model to use ('isolation_forest', 'lof', or 'both')
        
    Returns:
        DataFrame with original data and anomaly scores/predictions
    """
    return anomaly_detector.detect_anomalies(normalized_data, threshold, model)
