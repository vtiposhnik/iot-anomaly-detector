"""
Feature Extractor for Network Traffic Data

This module provides functions for extracting features from network traffic data
for use in anomaly detection models. It is designed to work with any network traffic data
that has been normalized by our adapters.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import joblib
import os
from utils.logger import get_logger

# Get logger
logger = get_logger()

# Constants
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
SCALER_PATH = os.path.join(MODELS_DIR, 'scaler.pkl')
ENCODER_PATH = os.path.join(MODELS_DIR, 'encoder.pkl')

# Ensure models directory exists
os.makedirs(MODELS_DIR, exist_ok=True)

class FeatureExtractor:
    """
    Class for extracting features from network traffic data.
    
    This class provides methods for extracting features from normalized network
    traffic data and preparing them for use in anomaly detection models.
    """
    
    def __init__(self):
        """Initialize the feature extractor"""
        self.scaler = None
        self.encoder = None
        self.feature_names = []
        
        # Try to load existing scaler and encoder
        self._load_transformers()
    
    def _load_transformers(self):
        """Load existing scaler and encoder if available"""
        try:
            if os.path.exists(SCALER_PATH):
                self.scaler = joblib.load(SCALER_PATH)
                logger.info(f"Loaded scaler from {SCALER_PATH}")
            
            if os.path.exists(ENCODER_PATH):
                self.encoder = joblib.load(ENCODER_PATH)
                logger.info(f"Loaded encoder from {ENCODER_PATH}")
        except Exception as e:
            logger.warning(f"Error loading transformers: {str(e)}")
    
    def _save_transformers(self):
        """Save scaler and encoder for future use"""
        try:
            if self.scaler:
                joblib.dump(self.scaler, SCALER_PATH)
                logger.info(f"Saved scaler to {SCALER_PATH}")
            
            if self.encoder:
                joblib.dump(self.encoder, ENCODER_PATH)
                logger.info(f"Saved encoder to {ENCODER_PATH}")
        except Exception as e:
            logger.warning(f"Error saving transformers: {str(e)}")
    
    def extract_basic_features(self, df):
        """
        Extract basic features from normalized network traffic data
        
        Args:
            df: Pandas DataFrame with normalized network traffic data
            
        Returns:
            Pandas DataFrame with extracted features
        """
        # Make a copy to avoid modifying the original
        features_df = pd.DataFrame()
        
        # 1. Bytes ratio (orig_bytes / resp_bytes)
        features_df['bytes_ratio'] = df.apply(
            lambda x: x['orig_bytes'] / max(x['resp_bytes'], 1),
            axis=1
        )
        
        # 2. Packet rate (packet_size / duration)
        features_df['packet_rate'] = df.apply(
            lambda x: x['packet_size'] / max(x['duration'], 0.001),
            axis=1
        )
        
        # 3. Log-transformed features (to handle skewed distributions)
        features_df['log_duration'] = np.log1p(df['duration'])
        features_df['log_orig_bytes'] = np.log1p(df['orig_bytes'])
        features_df['log_resp_bytes'] = np.log1p(df['resp_bytes'])
        features_df['log_packet_size'] = np.log1p(df['packet_size'])
        
        # 4. Port ranges (well-known, registered, dynamic)
        features_df['src_port_type'] = df['src_port'].apply(self._categorize_port)
        features_df['dst_port_type'] = df['dst_port'].apply(self._categorize_port)
        
        # 5. Protocol one-hot encoding
        if self.encoder is None:
            # Create a new encoder if not loaded
            self.encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
            protocol_df = pd.DataFrame(self.encoder.fit_transform(df[['protocol']]))
            protocol_categories = self.encoder.categories_[0]
            protocol_df.columns = [f'protocol_{cat}' for cat in protocol_categories]
            self._save_transformers()
        else:
            # Use existing encoder
            protocol_df = pd.DataFrame(self.encoder.transform(df[['protocol']]))
            protocol_categories = self.encoder.categories_[0]
            protocol_df.columns = [f'protocol_{cat}' for cat in protocol_categories]
        
        # Add protocol features to the main features DataFrame
        for col in protocol_df.columns:
            features_df[col] = protocol_df[col].values
        
        # Store feature names
        self.feature_names = features_df.columns.tolist()
        
        return features_df
    
    def extract_advanced_features(self, df):
        """
        Extract advanced features from normalized network traffic data
        
        Args:
            df: Pandas DataFrame with normalized network traffic data
            
        Returns:
            Pandas DataFrame with extracted features
        """
        # Start with basic features
        features_df = self.extract_basic_features(df)
        
        # Add more advanced features if the data is available
        
        # 6. Time-based features (if timestamp is available)
        if 'timestamp' in df.columns and pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            # Hour of day (cyclical encoding)
            hour = df['timestamp'].dt.hour
            features_df['hour_sin'] = np.sin(2 * np.pi * hour / 24)
            features_df['hour_cos'] = np.cos(2 * np.pi * hour / 24)
            
            # Day of week (cyclical encoding)
            day = df['timestamp'].dt.dayofweek
            features_df['day_sin'] = np.sin(2 * np.pi * day / 7)
            features_df['day_cos'] = np.cos(2 * np.pi * day / 7)
            
            # Time window aggregations - useful for detecting bursts and patterns
            if len(df) > 10:  # Only if we have enough data
                # Sort by timestamp
                df_sorted = df.sort_values('timestamp')
                
                # Create time windows
                df_sorted['time_window'] = pd.cut(df_sorted['timestamp'], 
                                                 bins=min(10, len(df_sorted) // 5))
                
                # Aggregate by time window
                aggs = df_sorted.groupby('time_window').agg({
                    'packet_size': ['mean', 'std', 'count'],
                    'duration': ['mean', 'sum']
                }).reset_index()
                
                # Flatten the column names
                aggs.columns = ['_'.join(col).strip() for col in aggs.columns.values]
                
                # Merge back to original data
                df_sorted = pd.merge(df_sorted, aggs, left_on='time_window', right_on='time_window_')
                
                # Add to features
                features_df['packets_per_window'] = df_sorted['packet_size_count'].values
                features_df['avg_packet_size_window'] = df_sorted['packet_size_mean'].values
                features_df['std_packet_size_window'] = df_sorted['packet_size_std'].fillna(0).values
                features_df['total_duration_window'] = df_sorted['duration_sum'].values
        
        # 7. Connection state features (if available)
        if 'conn_state' in df.columns:
            # One-hot encode connection state
            conn_state_dummies = pd.get_dummies(df['conn_state'], prefix='conn_state')
            for col in conn_state_dummies.columns:
                features_df[col] = conn_state_dummies[col].values
            
            # Add connection state transition features
            if len(df) > 1:
                # Count transitions between states
                transitions = {}
                prev_states = df['conn_state'].iloc[:-1].values
                curr_states = df['conn_state'].iloc[1:].values
                
                for prev, curr in zip(prev_states, curr_states):
                    transition = f"{prev}_to_{curr}"
                    transitions[transition] = transitions.get(transition, 0) + 1
                
                # Normalize by total transitions
                total = sum(transitions.values())
                for transition, count in transitions.items():
                    features_df[f'trans_{transition}'] = count / total
        
        # 8. Service features (if available)
        if 'service' in df.columns:
            # Group services into categories
            features_df['is_web'] = df['service'].apply(
                lambda x: 1 if x in ['http', 'https', 'ssl', 'web'] else 0
            )
            features_df['is_mail'] = df['service'].apply(
                lambda x: 1 if x in ['smtp', 'pop3', 'imap'] else 0
            )
            features_df['is_dns'] = df['service'].apply(
                lambda x: 1 if x == 'dns' else 0
            )
            features_df['is_file_transfer'] = df['service'].apply(
                lambda x: 1 if x in ['ftp', 'sftp', 'tftp'] else 0
            )
            
            # Service diversity - number of unique services per device
            if 'device_id' in df.columns:
                service_counts = df.groupby('device_id')['service'].nunique()
                features_df['service_diversity'] = df['device_id'].map(service_counts)
        
        # 9. Network flow features
        if all(col in df.columns for col in ['src_ip', 'dst_ip', 'src_port', 'dst_port']):
            # Create flow identifiers
            df['flow_id'] = df.apply(
                lambda x: f"{x['src_ip']}:{x['src_port']}-{x['dst_ip']}:{x['dst_port']}", 
                axis=1
            )
            
            # Count flows per source/destination
            src_flow_counts = df.groupby('src_ip')['flow_id'].nunique()
            dst_flow_counts = df.groupby('dst_ip')['flow_id'].nunique()
            
            features_df['src_flow_count'] = df['src_ip'].map(src_flow_counts)
            features_df['dst_flow_count'] = df['dst_ip'].map(dst_flow_counts)
            
            # Flow size features
            flow_sizes = df.groupby('flow_id')['packet_size'].sum()
            features_df['flow_size'] = df['flow_id'].map(flow_sizes)
            
            # Flow duration
            if 'timestamp' in df.columns and pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                flow_durations = df.groupby('flow_id').apply(
                    lambda x: (x['timestamp'].max() - x['timestamp'].min()).total_seconds()
                    if len(x) > 1 else 0
                )
                features_df['flow_duration'] = df['flow_id'].map(flow_durations)
        
        # 10. IoT-specific features
        # Detect periodic behavior (common in IoT devices)
        if 'timestamp' in df.columns and pd.api.types.is_datetime64_any_dtype(df['timestamp']) and 'device_id' in df.columns:
            # Group by device
            for device_id, device_df in df.groupby('device_id'):
                if len(device_df) > 5:  # Need enough data points
                    # Sort by timestamp
                    device_df = device_df.sort_values('timestamp')
                    
                    # Calculate time differences between consecutive packets
                    time_diffs = device_df['timestamp'].diff().dt.total_seconds().dropna()
                    
                    if not time_diffs.empty:
                        # Calculate coefficient of variation (std/mean) of time differences
                        # Low values indicate periodic behavior
                        cv = time_diffs.std() / time_diffs.mean() if time_diffs.mean() > 0 else 0
                        
                        # Add to features
                        features_df.loc[df['device_id'] == device_id, 'time_diff_cv'] = cv
        
        # Update feature names
        self.feature_names = features_df.columns.tolist()
        
        return features_df
    
    def normalize_features(self, features_df, training=False):
        """
        Normalize features for model training/inference
        
        Args:
            features_df: DataFrame containing features
            training: Boolean indicating if this is for training (will fit scaler)
            
        Returns:
            Normalized features as numpy array
        """
        # Convert to numpy array
        features = features_df.values
        
        if training or self.scaler is None:
            # Fit a new scaler if training or none exists
            self.scaler = StandardScaler()
            normalized_features = self.scaler.fit_transform(features)
            self._save_transformers()
        else:
            # Use existing scaler
            normalized_features = self.scaler.transform(features)
        
        return normalized_features
    
    def _categorize_port(self, port):
        """
        Categorize port number into well-known, registered, or dynamic
        
        Args:
            port: Port number
            
        Returns:
            Category as integer (0: well-known, 1: registered, 2: dynamic)
        """
        if port < 1024:
            return 0  # Well-known ports
        elif port < 49152:
            return 1  # Registered ports
        else:
            return 2  # Dynamic/private ports

# Create a singleton instance
feature_extractor = FeatureExtractor()

def extract_features(df, advanced=True, normalize=True, training=False):
    """
    Extract features from normalized network traffic data
    
    Args:
        df: Pandas DataFrame with normalized network traffic data
        advanced: Boolean indicating whether to extract advanced features
        normalize: Boolean indicating whether to normalize features
        training: Boolean indicating if this is for training (will fit transformers)
        
    Returns:
        Tuple of (features, feature_names)
    """
    try:
        # Extract features
        if advanced:
            features_df = feature_extractor.extract_advanced_features(df)
        else:
            features_df = feature_extractor.extract_basic_features(df)
        
        # Get feature names
        feature_names = feature_extractor.feature_names
        
        # Normalize if requested
        if normalize:
            features = feature_extractor.normalize_features(features_df, training)
            return features, feature_names
        else:
            return features_df.values, feature_names
    
    except Exception as e:
        logger.error(f"Error extracting features: {str(e)}")
        raise
