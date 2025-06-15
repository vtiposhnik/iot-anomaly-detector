"""
Anomaly Detection CLI

This script demonstrates the full anomaly detection pipeline, from data ingestion
to anomaly detection and result output.
"""
import os
import argparse
import pandas as pd
from datetime import datetime
from adapters.adapter_factory import create_adapter
from ml.generic_anomaly_detector import detect_anomalies
from utils.logger import get_logger
from utils.config import get_config
from utils.database import insert_anomalies

# Get logger
logger = get_logger()

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Detect anomalies in network traffic data')
    
    parser.add_argument('--input', type=str, required=True,
                        help='Path to input data file')
    
    parser.add_argument('--adapter', type=str, default=None,
                        choices=['csv', 'json', 'pcap', 'iot23'],
                        help='Type of adapter to use (default: auto-detect)')
    
    parser.add_argument('--threshold', type=float,
                        default=get_config('anomaly_detection.default_threshold', 0.7),
                        help='Threshold for anomaly detection')
    
    parser.add_argument('--model', type=str,
                        default=get_config('anomaly_detection.default_model', 'both'),
                        choices=['isolation_forest', 'lof', 'both'],
                        help='Model to use for anomaly detection')
    
    parser.add_argument('--output', type=str, default=None,
                        help='Path to output CSV file (optional)')
    
    parser.add_argument('--save-to-db', action='store_true',
                        help='Save detected anomalies to database')
    
    return parser.parse_args()

def main():
    """Main function"""
    # Parse arguments
    args = parse_args()
    
    logger.info(f"Detecting anomalies in {args.input}")
    
    try:
        # Create adapter
        adapter = create_adapter(args.input, args.adapter)
        
        # Load and normalize data
        logger.info("Loading and normalizing data...")
        normalized_data = adapter.process(args.input)
        
        logger.info(f"Normalized data shape: {normalized_data.shape}")
        
        # Detect anomalies
        logger.info(f"Detecting anomalies with model={args.model}, threshold={args.threshold}...")
        result = detect_anomalies(normalized_data, args.threshold, args.model)
        
        # Extract anomalies
        anomalies = result[result['is_anomaly']].copy()
        
        # Print summary
        logger.info(f"Detected {len(anomalies)} anomalies in {len(normalized_data)} records "
                   f"({len(anomalies) / len(normalized_data) * 100:.2f}%)")
        
        # Save to database if requested
        if args.save_to_db:
            logger.info("Saving anomalies to database...")
            insert_anomalies(anomalies)
        
        # Save to CSV if output path provided
        if args.output:
            logger.info(f"Saving results to {args.output}...")
            result.to_csv(args.output, index=False)
        
        # Print first few anomalies
        if len(anomalies) > 0:
            print("\nSample of detected anomalies:")
            pd.set_option('display.max_columns', None)
            print(anomalies.head().to_string())
        
        return 0
    
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
