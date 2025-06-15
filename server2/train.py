"""
Training Script for Anomaly Detection Models

This script trains anomaly detection models on network traffic data from any source.
It uses our adapter system to normalize the data and our feature extractor to prepare
it for training.
"""
import os
import argparse
import pandas as pd
from datetime import datetime
from adapters.adapter_factory import create_adapter
from ml.generic_anomaly_detector import train_models
from utils.logger import get_logger

# Get logger
logger = get_logger()

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Train anomaly detection models')
    
    parser.add_argument('--input', type=str, required=True,
                        help='Path to input data file')
    
    parser.add_argument('--adapter', type=str, default=None,
                        choices=['csv', 'json', 'pcap', 'iot23'],
                        help='Type of adapter to use (default: auto-detect)')
    
    parser.add_argument('--output-dir', type=str, default='models',
                        help='Directory to save trained models')
    
    parser.add_argument('--contamination', type=float, default=0.1,
                        help='Expected proportion of anomalies in the data')
    
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of samples to use for training')
    
    return parser.parse_args()

def main():
    """Main function"""
    # Parse arguments
    args = parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    logger.info(f"Training models with data from {args.input}")
    
    try:
        # Create adapter
        adapter = create_adapter(args.input, args.adapter)
        
        # Load and normalize data
        logger.info("Loading and normalizing data...")
        normalized_data = adapter.process(args.input)
        
        # Limit samples if requested
        if args.limit and len(normalized_data) > args.limit:
            logger.info(f"Limiting to {args.limit} samples")
            normalized_data = normalized_data.sample(args.limit, random_state=42)
        
        logger.info(f"Normalized data shape: {normalized_data.shape}")
        
        # Train models
        logger.info(f"Training models with contamination={args.contamination}...")
        success = train_models(normalized_data, args.contamination)
        
        if success:
            logger.info("Training completed successfully!")
        else:
            logger.error("Training failed")
    
    except Exception as e:
        logger.error(f"Error during training: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
