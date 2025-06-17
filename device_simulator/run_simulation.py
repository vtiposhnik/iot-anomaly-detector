"""
Run IoT Device Simulation

This script provides a command-line interface for running the IoT device simulator
with different options and modes.
"""
import argparse
import logging
import sys
import os

# Add current directory to path for module imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from device_simulator import IoTDeviceSimulator
from config import (
    MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_USERNAME,
    MQTT_PASSWORD, MQTT_QOS, DATASET_PATH,
    DEFAULT_INTERVAL, DEFAULT_RECORDS_PER_DEVICE, GLOBAL_INTERVAL,
    LOG_LEVEL
)

def main():
    """Main function to run the IoT device simulator"""
    parser = argparse.ArgumentParser(description='IoT Device Simulator')
    
    # MQTT connection options
    parser.add_argument('--broker', type=str, default=MQTT_BROKER_HOST,
                        help=f'MQTT broker hostname or IP (default: {MQTT_BROKER_HOST})')
    parser.add_argument('--port', type=int, default=MQTT_BROKER_PORT,
                        help=f'MQTT broker port (default: {MQTT_BROKER_PORT})')
    parser.add_argument('--username', type=str, default=MQTT_USERNAME,
                        help='MQTT username (optional)')
    parser.add_argument('--password', type=str, default=MQTT_PASSWORD,
                        help='MQTT password (optional)')
    parser.add_argument('--qos', type=int, default=MQTT_QOS,
                        help=f'MQTT Quality of Service level (default: {MQTT_QOS})')
    
    # Dataset options
    parser.add_argument('--dataset', type=str, default=DATASET_PATH,
                        help=f'Path to dataset CSV file (default: {DATASET_PATH})')
    
    # Simulation mode options
    parser.add_argument('--mode', type=str, 
                        choices=['single', 'all', 'continuous', 'attack'],
                        default='continuous', 
                        help='Simulation mode (default: continuous)')
    
    # Device options
    parser.add_argument('--device', type=int, default=None,
                        help='Device ID to simulate (for single mode)')
    
    # Timing options
    parser.add_argument('--interval', type=float, default=DEFAULT_INTERVAL,
                        help=f'Interval between messages in seconds (default: {DEFAULT_INTERVAL})')
    parser.add_argument('--count', type=int, default=DEFAULT_RECORDS_PER_DEVICE,
                        help=f'Number of records to send per device (default: {DEFAULT_RECORDS_PER_DEVICE})')
    parser.add_argument('--global-interval', type=float, default=GLOBAL_INTERVAL,
                        help=f'Interval between device simulations in seconds (default: {GLOBAL_INTERVAL})')
    
    # Attack simulation options
    parser.add_argument('--attack-type', type=str, default=None,
                        help='Type of attack to simulate (for attack mode)')
    parser.add_argument('--duration', type=int, default=60,
                        help='Duration of attack simulation in seconds (default: 60)')
    
    # Logging options
    parser.add_argument('--log-level', type=str, 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default=LOG_LEVEL,
                        help=f'Logging level (default: {LOG_LEVEL})')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('run_simulation')
    
    # Create simulator
    try:
        simulator = IoTDeviceSimulator(
            broker_host=args.broker,
            broker_port=args.port,
            username=args.username,
            password=args.password,
            qos=args.qos,
            dataset_path=args.dataset
        )
    except Exception as e:
        logger.error(f"Failed to create simulator: {str(e)}")
        return 1
    
    # Connect to broker
    if not simulator.connect():
        logger.error("Failed to connect to MQTT broker")
        return 1
    
    # Run simulation based on mode
    try:
        if args.mode == 'single':
            if args.device is None:
                logger.error("Device ID must be specified for single mode")
                return 1
            
            logger.info(f"Simulating device {args.device} with interval {args.interval}s and count {args.count}")
            simulator.simulate_device(args.device, args.interval, args.count)
        
        elif args.mode == 'all':
            logger.info(f"Simulating all devices with interval {args.interval}s and count {args.count}")
            simulator.simulate_all_devices(args.interval, args.count)
        
        elif args.mode == 'attack':
            logger.info(f"Simulating attack pattern {args.attack_type or 'random'} for {args.duration}s")
            simulator.simulate_attack_pattern(args.attack_type, args.duration)
        
        else:  # continuous
            logger.info(f"Running continuous simulation with global interval {args.global_interval}s")
            simulator.run_continuous_simulation(args.global_interval)
    
    except KeyboardInterrupt:
        logger.info("Simulation stopped by user")
    
    except Exception as e:
        logger.error(f"Error during simulation: {str(e)}")
        return 1
    
    finally:
        # Disconnect from broker
        simulator.disconnect()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
