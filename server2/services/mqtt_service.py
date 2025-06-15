"""
MQTT Service for Real-Time IoT Monitoring

This module provides a service for managing MQTT connections and processing
real-time data from IoT devices.
"""
import os
import threading
import time
from adapters.mqtt_adapter import MQTTAdapter
from utils.logger import get_logger
from utils.config import get_config

# Get logger
logger = get_logger()

class MQTTService:
    """
    Service for managing MQTT connections and processing real-time data.
    
    This service creates and manages MQTT adapters for different brokers
    and handles the lifecycle of MQTT connections.
    """
    
    def __init__(self):
        """Initialize the MQTT service"""
        self.adapters = {}
        self.running = False
        self.thread = None
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load MQTT configuration from config file"""
        # Default configuration
        self.default_broker_host = get_config('mqtt.broker_host', 'localhost')
        self.default_broker_port = get_config('mqtt.broker_port', 1883)
        self.default_topics = get_config('mqtt.topics', ['iot/+/data'])
        self.default_username = get_config('mqtt.username', None)
        self.default_password = get_config('mqtt.password', None)
        self.default_qos = get_config('mqtt.qos', 0)
        self.buffer_size = get_config('mqtt.buffer_size', 10)
        self.auto_start = get_config('mqtt.auto_start', False)
        
        # Load broker configurations
        self.broker_configs = get_config('mqtt.brokers', [])
        
        # If no brokers configured, add default broker
        if not self.broker_configs:
            self.broker_configs = [{
                'name': 'default',
                'host': self.default_broker_host,
                'port': self.default_broker_port,
                'topics': self.default_topics,
                'username': self.default_username,
                'password': self.default_password,
                'qos': self.default_qos
            }]
    
    def start(self):
        """
        Start the MQTT service
        
        Returns:
            Boolean indicating success
        """
        if self.running:
            logger.warning("MQTT service is already running")
            return True
        
        try:
            logger.info("Starting MQTT service")
            
            # Create and start adapters for all configured brokers
            for broker_config in self.broker_configs:
                self.add_broker(
                    name=broker_config.get('name', 'default'),
                    host=broker_config.get('host', self.default_broker_host),
                    port=broker_config.get('port', self.default_broker_port),
                    topics=broker_config.get('topics', self.default_topics),
                    username=broker_config.get('username', self.default_username),
                    password=broker_config.get('password', self.default_password),
                    qos=broker_config.get('qos', self.default_qos)
                )
            
            # Start monitoring thread
            self.running = True
            self.thread = threading.Thread(target=self._monitor_thread, daemon=True)
            self.thread.start()
            
            logger.info("MQTT service started successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error starting MQTT service: {str(e)}")
            self.stop()
            return False
    
    def stop(self):
        """
        Stop the MQTT service
        
        Returns:
            Boolean indicating success
        """
        if not self.running:
            logger.warning("MQTT service is not running")
            return True
        
        try:
            logger.info("Stopping MQTT service")
            
            # Stop all adapters
            for name, adapter in list(self.adapters.items()):
                self.remove_broker(name)
            
            # Stop monitoring thread
            self.running = False
            if self.thread:
                self.thread.join(timeout=5)
                self.thread = None
            
            logger.info("MQTT service stopped successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping MQTT service: {str(e)}")
            return False
    
    def add_broker(self, name, host, port=1883, topics=None, username=None, password=None, qos=0):
        """
        Add a new MQTT broker
        
        Args:
            name: Unique name for the broker
            host: Broker hostname or IP
            port: Broker port
            topics: List of topics to subscribe to
            username: MQTT username (optional)
            password: MQTT password (optional)
            qos: Quality of Service level
        
        Returns:
            Boolean indicating success
        """
        try:
            # Check if broker with this name already exists
            if name in self.adapters:
                logger.warning(f"Broker '{name}' already exists, removing first")
                self.remove_broker(name)
            
            # Create adapter
            adapter = MQTTAdapter(
                broker_host=host,
                broker_port=port,
                topics=topics,
                username=username,
                password=password,
                qos=qos,
                client_id=f"iot_anomaly_detector_{name}"
            )
            
            # Start adapter
            if adapter.start():
                self.adapters[name] = adapter
                logger.info(f"Added MQTT broker '{name}' at {host}:{port}")
                return True
            else:
                logger.error(f"Failed to start adapter for broker '{name}'")
                return False
        
        except Exception as e:
            logger.error(f"Error adding MQTT broker '{name}': {str(e)}")
            return False
    
    def remove_broker(self, name):
        """
        Remove an MQTT broker
        
        Args:
            name: Name of the broker to remove
        
        Returns:
            Boolean indicating success
        """
        try:
            if name in self.adapters:
                # Stop adapter
                adapter = self.adapters[name]
                adapter.stop()
                
                # Remove from adapters
                del self.adapters[name]
                
                logger.info(f"Removed MQTT broker '{name}'")
                return True
            else:
                logger.warning(f"Broker '{name}' not found")
                return False
        
        except Exception as e:
            logger.error(f"Error removing MQTT broker '{name}': {str(e)}")
            return False
    
    def get_broker_status(self, name=None):
        """
        Get status of MQTT brokers
        
        Args:
            name: Name of specific broker to check (optional)
        
        Returns:
            Dictionary with broker status information
        """
        try:
            if name:
                # Get status of specific broker
                if name in self.adapters:
                    adapter = self.adapters[name]
                    return {
                        'name': name,
                        'connected': adapter.connected,
                        'host': adapter.broker_host,
                        'port': adapter.broker_port,
                        'topics': adapter.topics
                    }
                else:
                    return {'error': f"Broker '{name}' not found"}
            else:
                # Get status of all brokers
                return {
                    name: {
                        'connected': adapter.connected,
                        'host': adapter.broker_host,
                        'port': adapter.broker_port,
                        'topics': adapter.topics
                    }
                    for name, adapter in self.adapters.items()
                }
        
        except Exception as e:
            logger.error(f"Error getting broker status: {str(e)}")
            return {'error': str(e)}
    
    def _monitor_thread(self):
        """Thread for monitoring MQTT adapters"""
        logger.info("MQTT monitoring thread started")
        
        while self.running:
            try:
                # Check status of all adapters
                for name, adapter in list(self.adapters.items()):
                    if not adapter.connected:
                        logger.warning(f"Broker '{name}' disconnected, attempting to reconnect")
                        # Try to reconnect
                        adapter.stop()
                        adapter.start()
                
                # Sleep for a while
                time.sleep(60)
            
            except Exception as e:
                logger.error(f"Error in MQTT monitoring thread: {str(e)}")
                time.sleep(10)
        
        logger.info("MQTT monitoring thread stopped")

# Singleton instance
_instance = None

def get_mqtt_service():
    """
    Get the singleton MQTT service instance
    
    Returns:
        MQTTService instance
    """
    global _instance
    if _instance is None:
        _instance = MQTTService()
    return _instance
