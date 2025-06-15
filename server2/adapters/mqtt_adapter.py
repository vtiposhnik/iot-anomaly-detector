"""
MQTT Adapter for Real-Time IoT Data Ingestion

This module provides an adapter for receiving and processing data from MQTT brokers,
enabling real-time monitoring of IoT devices.
"""
import json
import pandas as pd
from datetime import datetime
import paho.mqtt.client as mqtt
from .base_adapter import BaseAdapter
from utils.logger import get_logger
from utils.config import get_config

# Get logger
logger = get_logger()

class MQTTAdapter(BaseAdapter):
    """
    Adapter for MQTT data sources.
    
    This adapter connects to an MQTT broker and subscribes to topics
    to receive real-time data from IoT devices.
    """
    
    def __init__(self, broker_host="localhost", broker_port=1883, 
                 topics=None, username=None, password=None,
                 qos=0, client_id="iot_anomaly_detector"):
        """
        Initialize the MQTT adapter
        
        Args:
            broker_host: MQTT broker hostname or IP
            broker_port: MQTT broker port
            topics: List of topics to subscribe to (default: ["iot/+/data"])
            username: MQTT username (optional)
            password: MQTT password (optional)
            qos: Quality of Service level
            client_id: MQTT client ID
        """
        super().__init__()
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topics = topics or ["iot/+/data"]
        self.username = username
        self.password = password
        self.qos = qos
        self.client_id = client_id
        self.client = None
        self.connected = False
        self.threshold = get_config('anomaly_detection.default_threshold', 0.7)
        self.model = get_config('anomaly_detection.default_model', 'both')
        
        # Buffer for collecting messages before processing
        self.message_buffer = []
        self.buffer_size = get_config('mqtt.buffer_size', 10)
        
    def load_data(self, source_path=None):
        """
        Not used in MQTT adapter as data comes from broker
        
        Args:
            source_path: Not used
            
        Returns:
            Empty DataFrame
        """
        # This method is not used in MQTT adapter
        return pd.DataFrame()
    
    def normalize(self, raw_data):
        """
        Normalize MQTT message data into standard format
        
        Args:
            raw_data: Dictionary containing MQTT message data
            
        Returns:
            Pandas DataFrame with normalized data
        """
        try:
            # Create a DataFrame with a single row
            df = pd.DataFrame([raw_data])
            
            # Ensure timestamp is in datetime format
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            else:
                df['timestamp'] = pd.Timestamp.now()
            
            # Extract device_id from topic if not in data
            if 'device_id' not in df.columns and 'topic' in raw_data:
                topic_parts = raw_data['topic'].split('/')
                if len(topic_parts) >= 2:
                    try:
                        df['device_id'] = int(topic_parts[1])
                    except ValueError:
                        df['device_id'] = 0
                else:
                    df['device_id'] = 0
            
            return df
        
        except Exception as e:
            logger.error(f"Error normalizing MQTT data: {str(e)}")
            # Return empty DataFrame on error
            return pd.DataFrame()
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback for when the client connects to the broker
        
        Args:
            client: MQTT client instance
            userdata: User data
            flags: Connection flags
            rc: Connection result code
        """
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.connected = True
            
            # Subscribe to all configured topics
            for topic in self.topics:
                client.subscribe(topic, qos=self.qos)
                logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
            self.connected = False
    
    def _on_message(self, client, userdata, msg):
        """
        Callback for when a message is received from the broker
        
        Args:
            client: MQTT client instance
            userdata: User data
            msg: MQTT message
        """
        try:
            # Decode message payload
            payload = msg.payload.decode('utf-8')
            logger.debug(f"Received message on topic {msg.topic}: {payload}")
            
            # Parse JSON payload
            data = json.loads(payload)
            
            # Add topic to data for device_id extraction
            data['topic'] = msg.topic
            
            # Add to buffer
            self.message_buffer.append(data)
            
            # Process buffer if it reaches the threshold
            if len(self.message_buffer) >= self.buffer_size:
                self._process_buffer()
        
        except json.JSONDecodeError:
            logger.warning(f"Received non-JSON message on topic {msg.topic}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {str(e)}")
    
    def _process_buffer(self):
        """Process the message buffer and detect anomalies"""
        if not self.message_buffer:
            return
        
        try:
            # Normalize all messages in buffer
            normalized_data = pd.DataFrame()
            for msg in self.message_buffer:
                df = self.normalize(msg)
                if not df.empty:
                    normalized_data = pd.concat([normalized_data, df], ignore_index=True)
            
            # Clear buffer
            self.message_buffer = []
            
            if normalized_data.empty:
                logger.warning("No valid data to process in buffer")
                return
            
            # Ensure schema
            normalized_data = self.ensure_schema(normalized_data)
            
            # Detect anomalies
            logger.info(f"Detecting anomalies in {len(normalized_data)} records...")
            
            # Import here to avoid circular imports
            from ml.generic_anomaly_detector import detect_anomalies
            from utils.database import insert_anomalies
            
            result = detect_anomalies(normalized_data, self.threshold, self.model)
            
            # Extract anomalies
            anomalies = result[result['is_anomaly']].copy()
            
            # Process and store anomalies
            if not anomalies.empty:
                anomaly_count = len(anomalies)
                logger.info(f"Detected {anomaly_count} anomalies in real-time data")
                
                # Store anomalies in database
                insert_anomalies(anomalies)
        
        except Exception as e:
            logger.error(f"Error processing message buffer: {str(e)}")
    
    def start(self):
        """
        Start the MQTT client and connect to the broker
        
        Returns:
            Boolean indicating success
        """
        try:
            # Create MQTT client
            self.client = mqtt.Client(client_id=self.client_id)
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            
            # Set authentication if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Connect to broker
            logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port)
            
            # Start the loop in a non-blocking way
            self.client.loop_start()
            
            return True
        
        except Exception as e:
            logger.error(f"Error starting MQTT adapter: {str(e)}")
            return False
    
    def stop(self):
        """
        Stop the MQTT client
        
        Returns:
            Boolean indicating success
        """
        try:
            if self.client:
                # Process any remaining messages in buffer
                self._process_buffer()
                
                # Disconnect and stop loop
                self.client.loop_stop()
                self.client.disconnect()
                logger.info("MQTT adapter stopped")
            
            return True
        
        except Exception as e:
            logger.error(f"Error stopping MQTT adapter: {str(e)}")
            return False
    
    def set_threshold(self, threshold):
        """
        Set the anomaly detection threshold
        
        Args:
            threshold: New threshold value
        """
        self.threshold = threshold
    
    def set_model(self, model):
        """
        Set the anomaly detection model
        
        Args:
            model: Model to use ('isolation_forest', 'lof', or 'both')
        """
        self.model = model
