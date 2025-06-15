"""
Feedback Loop for Anomaly Detection Models

This module provides functionality for incorporating user feedback into
anomaly detection models, enabling them to learn from past detections
and improve over time.
"""
import os
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from utils.logger import get_logger
from utils.database import get_db_connection
from utils.config import get_config
from ml.feature_extractor import extract_features

# Get logger
logger = get_logger()

# Constants
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
FEEDBACK_DIR = os.path.join(MODELS_DIR, 'feedback')
HISTORY_FILE = os.path.join(FEEDBACK_DIR, 'feedback_history.csv')
IF_MODEL_PATH = os.path.join(MODELS_DIR, 'isolation_forest.pkl')
LOF_MODEL_PATH = os.path.join(MODELS_DIR, 'local_outlier_factor.pkl')

# Ensure directories exist
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(FEEDBACK_DIR, exist_ok=True)

class FeedbackLoop:
    """
    Class for managing the feedback loop for anomaly detection models.
    
    This class provides methods for recording feedback, updating models
    based on feedback, and scheduling regular retraining.
    """
    
    def __init__(self):
        """Initialize the feedback loop"""
        self.feedback_history = self._load_feedback_history()
        self.last_retrain_time = self._get_last_retrain_time()
        self.retrain_interval = get_config('ml.retrain_interval_days', 7)
        self.min_feedback_count = get_config('ml.min_feedback_count', 10)
        self.max_feedback_age = get_config('ml.max_feedback_age_days', 90)
    
    def _load_feedback_history(self):
        """Load feedback history from file"""
        try:
            if os.path.exists(HISTORY_FILE):
                return pd.read_csv(HISTORY_FILE)
            else:
                # Create empty feedback history
                return pd.DataFrame(columns=[
                    'anomaly_id', 'log_id', 'device_id', 'timestamp',
                    'is_genuine', 'feedback_time', 'model_used'
                ])
        except Exception as e:
            logger.error(f"Error loading feedback history: {str(e)}")
            return pd.DataFrame(columns=[
                'anomaly_id', 'log_id', 'device_id', 'timestamp',
                'is_genuine', 'feedback_time', 'model_used'
            ])
    
    def _save_feedback_history(self):
        """Save feedback history to file"""
        try:
            self.feedback_history.to_csv(HISTORY_FILE, index=False)
            logger.info(f"Saved feedback history to {HISTORY_FILE}")
        except Exception as e:
            logger.error(f"Error saving feedback history: {str(e)}")
    
    def _get_last_retrain_time(self):
        """Get the last time models were retrained"""
        try:
            # Check if models exist and get their modification time
            if os.path.exists(IF_MODEL_PATH):
                return datetime.fromtimestamp(os.path.getmtime(IF_MODEL_PATH))
            else:
                return datetime.min
        except Exception as e:
            logger.error(f"Error getting last retrain time: {str(e)}")
            return datetime.min
    
    def record_feedback(self, anomaly_id, is_genuine):
        """
        Record feedback for an anomaly detection
        
        Args:
            anomaly_id: ID of the anomaly
            is_genuine: Boolean indicating if the anomaly is genuine
            
        Returns:
            Boolean indicating success
        """
        try:
            # Get anomaly details from database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT * FROM anomalies WHERE anomaly_id = ?',
                (anomaly_id,)
            )
            anomaly = cursor.fetchone()
            
            if not anomaly:
                logger.warning(f"Anomaly with ID {anomaly_id} not found")
                return False
            
            # Update anomaly in database
            cursor.execute(
                'UPDATE anomalies SET is_genuine = ? WHERE anomaly_id = ?',
                (is_genuine, anomaly_id)
            )
            
            conn.commit()
            
            # Add to feedback history
            new_feedback = {
                'anomaly_id': anomaly_id,
                'log_id': anomaly['log_id'],
                'device_id': anomaly['device_id'],
                'timestamp': anomaly['detected_at'],
                'is_genuine': is_genuine,
                'feedback_time': datetime.now().isoformat(),
                'model_used': anomaly['model_used']
            }
            
            self.feedback_history = pd.concat([
                self.feedback_history, 
                pd.DataFrame([new_feedback])
            ], ignore_index=True)
            
            # Save feedback history
            self._save_feedback_history()
            
            # Check if we should retrain models
            self._check_retrain_models()
            
            logger.info(f"Recorded feedback for anomaly {anomaly_id}: is_genuine={is_genuine}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording feedback: {str(e)}")
            return False
    
    def _check_retrain_models(self):
        """Check if models should be retrained based on feedback"""
        try:
            # Check if enough time has passed since last retrain
            time_since_retrain = datetime.now() - self.last_retrain_time
            if time_since_retrain.days < self.retrain_interval:
                return False
            
            # Check if we have enough new feedback
            new_feedback = self.feedback_history[
                pd.to_datetime(self.feedback_history['feedback_time']) > self.last_retrain_time
            ]
            
            if len(new_feedback) < self.min_feedback_count:
                return False
            
            # Retrain models
            return self.retrain_models()
            
        except Exception as e:
            logger.error(f"Error checking retrain models: {str(e)}")
            return False
    
    def retrain_models(self, force=False):
        """
        Retrain anomaly detection models based on feedback
        
        Args:
            force: Boolean indicating if retraining should be forced
            
        Returns:
            Boolean indicating success
        """
        try:
            # Skip if not forced and not enough time has passed
            time_since_retrain = datetime.now() - self.last_retrain_time
            if not force and time_since_retrain.days < self.retrain_interval:
                logger.info("Skipping retraining: not enough time has passed")
                return False
            
            # Get recent feedback
            max_age = datetime.now() - timedelta(days=self.max_feedback_age)
            recent_feedback = self.feedback_history[
                pd.to_datetime(self.feedback_history['feedback_time']) > max_age
            ]
            
            if len(recent_feedback) < self.min_feedback_count and not force:
                logger.info("Skipping retraining: not enough feedback")
                return False
            
            logger.info(f"Retraining models with {len(recent_feedback)} feedback items")
            
            # Get traffic data for feedback items
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get log IDs from feedback
            log_ids = recent_feedback['log_id'].tolist()
            
            # Fetch traffic data
            cursor.execute(
                f'SELECT * FROM traffic WHERE log_id IN ({",".join(["?"] * len(log_ids))})',
                log_ids
            )
            traffic_data = [dict(row) for row in cursor.fetchall()]
            
            if not traffic_data:
                logger.warning("No traffic data found for feedback items")
                return False
            
            # Convert to DataFrame
            traffic_df = pd.DataFrame(traffic_data)
            
            # Ensure timestamp is datetime
            if 'timestamp' in traffic_df.columns:
                traffic_df['timestamp'] = pd.to_datetime(traffic_df['timestamp'])
            
            # Extract features
            features, feature_names = extract_features(
                traffic_df, advanced=True, normalize=True, training=True
            )
            
            # Split data based on feedback
            genuine_anomalies = recent_feedback[recent_feedback['is_genuine']]['log_id'].tolist()
            false_positives = recent_feedback[~recent_feedback['is_genuine']]['log_id'].tolist()
            
            # Create training labels (1 for genuine anomalies, -1 for false positives)
            labels = np.ones(len(traffic_df), dtype=int)
            labels[traffic_df['log_id'].isin(false_positives)] = -1
            
            # Train Isolation Forest model
            if_model = IsolationForest(
                n_estimators=100,
                contamination=0.1,
                random_state=42
            )
            if_model.fit(features)
            
            # Save model
            joblib.dump(if_model, IF_MODEL_PATH)
            
            # Train LOF model (note: LOF doesn't support partial_fit, so we just train a new model)
            lof_model = LocalOutlierFactor(
                n_neighbors=20,
                contamination=0.1,
                novelty=True
            )
            lof_model.fit(features)
            
            # Save model
            joblib.dump(lof_model, LOF_MODEL_PATH)
            
            # Update last retrain time
            self.last_retrain_time = datetime.now()
            
            logger.info("Models retrained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error retraining models: {str(e)}")
            return False
    
    def get_feedback_stats(self):
        """
        Get statistics about feedback
        
        Returns:
            Dictionary with feedback statistics
        """
        try:
            if self.feedback_history.empty:
                return {
                    'total_feedback': 0,
                    'genuine_anomalies': 0,
                    'false_positives': 0,
                    'last_retrain': self.last_retrain_time.isoformat() if self.last_retrain_time else None,
                    'feedback_by_model': {}
                }
            
            # Convert feedback_time to datetime
            self.feedback_history['feedback_time'] = pd.to_datetime(self.feedback_history['feedback_time'])
            
            # Calculate statistics
            total = len(self.feedback_history)
            genuine = self.feedback_history['is_genuine'].sum()
            false_positives = total - genuine
            
            # Feedback by model
            model_stats = self.feedback_history.groupby('model_used').agg({
                'is_genuine': ['count', 'sum']
            })
            
            model_stats.columns = ['_'.join(col).strip() for col in model_stats.columns.values]
            model_stats['false_positives'] = model_stats['is_genuine_count'] - model_stats['is_genuine_sum']
            
            # Convert to dictionary
            model_stats_dict = {}
            for model, row in model_stats.iterrows():
                model_stats_dict[model] = {
                    'total': int(row['is_genuine_count']),
                    'genuine': int(row['is_genuine_sum']),
                    'false_positives': int(row['false_positives'])
                }
            
            return {
                'total_feedback': total,
                'genuine_anomalies': int(genuine),
                'false_positives': int(false_positives),
                'last_retrain': self.last_retrain_time.isoformat() if self.last_retrain_time else None,
                'feedback_by_model': model_stats_dict
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback stats: {str(e)}")
            return {
                'total_feedback': 0,
                'genuine_anomalies': 0,
                'false_positives': 0,
                'last_retrain': None,
                'feedback_by_model': {},
                'error': str(e)
            }

# Create a singleton instance
feedback_loop = FeedbackLoop()

def record_anomaly_feedback(anomaly_id, is_genuine):
    """
    Record feedback for an anomaly detection
    
    Args:
        anomaly_id: ID of the anomaly
        is_genuine: Boolean indicating if the anomaly is genuine
        
    Returns:
        Boolean indicating success
    """
    return feedback_loop.record_feedback(anomaly_id, is_genuine)

def force_model_retrain():
    """
    Force retraining of anomaly detection models
    
    Returns:
        Boolean indicating success
    """
    return feedback_loop.retrain_models(force=True)

def get_feedback_statistics():
    """
    Get statistics about feedback
    
    Returns:
        Dictionary with feedback statistics
    """
    return feedback_loop.get_feedback_stats()
