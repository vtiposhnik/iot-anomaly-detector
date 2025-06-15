"""
MQTT API Routes

This module provides API endpoints for managing MQTT connections
and real-time IoT device monitoring.
"""
from flask import Blueprint, jsonify, request
from services.mqtt_service import get_mqtt_service
from utils.logger import get_logger

# Get logger
logger = get_logger()

# Create blueprint
mqtt_bp = Blueprint('mqtt', __name__, url_prefix='/api/v1/mqtt')

@mqtt_bp.route('/status', methods=['GET'])
def get_status():
    """Get status of MQTT service and connections"""
    mqtt_service = get_mqtt_service()
    
    # Get broker name from query parameter
    broker_name = request.args.get('broker', None)
    
    # Get status
    status = mqtt_service.get_broker_status(broker_name)
    
    # Add service status
    status['service_running'] = mqtt_service.running
    
    return jsonify(status)

@mqtt_bp.route('/start', methods=['POST'])
def start_service():
    """Start the MQTT service"""
    mqtt_service = get_mqtt_service()
    
    # Start service
    success = mqtt_service.start()
    
    if success:
        return jsonify({
            'status': 'success',
            'message': 'MQTT service started successfully'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to start MQTT service'
        }), 500

@mqtt_bp.route('/stop', methods=['POST'])
def stop_service():
    """Stop the MQTT service"""
    mqtt_service = get_mqtt_service()
    
    # Stop service
    success = mqtt_service.stop()
    
    if success:
        return jsonify({
            'status': 'success',
            'message': 'MQTT service stopped successfully'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to stop MQTT service'
        }), 500

@mqtt_bp.route('/broker', methods=['POST'])
def add_broker():
    """Add a new MQTT broker"""
    mqtt_service = get_mqtt_service()
    
    # Get broker details from request
    data = request.json
    
    if not data or 'name' not in data or 'host' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Missing required parameters: name, host'
        }), 400
    
    # Add broker
    success = mqtt_service.add_broker(
        name=data['name'],
        host=data['host'],
        port=data.get('port', 1883),
        topics=data.get('topics', None),
        username=data.get('username', None),
        password=data.get('password', None),
        qos=data.get('qos', 0)
    )
    
    if success:
        return jsonify({
            'status': 'success',
            'message': f"MQTT broker '{data['name']}' added successfully"
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f"Failed to add MQTT broker '{data['name']}'"
        }), 500

@mqtt_bp.route('/broker/<name>', methods=['DELETE'])
def remove_broker(name):
    """Remove an MQTT broker"""
    mqtt_service = get_mqtt_service()
    
    # Remove broker
    success = mqtt_service.remove_broker(name)
    
    if success:
        return jsonify({
            'status': 'success',
            'message': f"MQTT broker '{name}' removed successfully"
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f"Failed to remove MQTT broker '{name}'"
        }), 500
