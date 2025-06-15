"""
API Routes for the IoT Anomaly Detection System
"""
from flask import jsonify, request, Blueprint
from ml.anomaly_detector import detect_anomalies, get_model_status
from utils.logger import get_logger
from utils.database import get_devices, get_traffic, get_anomalies, add_anomaly, get_anomalies_by_timerange, get_anomaly_statistics
from utils.config import get_config

# Import the generic anomaly detection API endpoints
from api.generic_detect import generic_detect_bp

# Get logger
logger = get_logger()

# Create blueprints for API versioning
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

@api_v1.route('/status', methods=['GET'])
def status():
    """Return the status of the API and ML models"""
    return jsonify({
        'status': 'online',
        'model': get_model_status()
    })

@api_v1.route('/devices', methods=['GET'])
def get_all_devices():
    """Return a list of all monitored devices"""
    limit = request.args.get('limit', 100, type=int)
    devices = get_devices(limit=limit)
    
    # Enhance device data with more readable information
    for device in devices:
        device['name'] = f"Device {device['device_id']}"
        device['type'] = "IoT Device"
        device['location'] = "Network"
    
    return jsonify(devices)

@api_v1.route('/data', methods=['GET'])
def get_data():
    """Return sensor data, optionally filtered by device ID and time range"""
    limit = request.args.get('limit', 100, type=int)
    device_id = request.args.get('device_id', None, type=int)
    
    # Get traffic data from database
    traffic_data = get_traffic(limit=limit)
    
    # Filter by device ID if provided
    if device_id:
        traffic_data = [t for t in traffic_data if t['device_id'] == device_id]
    
    return jsonify(traffic_data)

@api_v1.route('/anomalies', methods=['GET'])
def get_all_anomalies():
    """Return detected anomalies, optionally filtered by device ID and time range"""
    limit = request.args.get('limit', 100, type=int)
    device_id = request.args.get('device_id', None, type=int)
    
    # Get time range parameters if provided
    start_time = request.args.get('start_time', None)
    end_time = request.args.get('end_time', None)
    
    # If time range is provided, use the time-based query
    if start_time and end_time:
        anomalies_data = get_anomalies_by_timerange(start_time, end_time, limit=limit)
    else:
        # Get anomalies from database
        anomalies_data = get_anomalies(limit=limit)
    
    # Filter by device ID if provided
    if device_id:
        anomalies_data = [a for a in anomalies_data if a['device_id'] == device_id]
    
    return jsonify(anomalies_data)

@api_v1.route('/statistics', methods=['GET'])
def get_statistics():
    """Return statistics about anomalies for dashboard visualization"""
    days = request.args.get('days', 7, type=int)
    
    # Get statistics from database
    statistics = get_anomaly_statistics(days=days)
    
    return jsonify(statistics)

@api_v1.route('/detect', methods=['POST'])
def detect():
    """Process new data and detect anomalies"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Process the incoming data through our anomaly detection pipeline
        anomalies = detect_anomalies(data)
        
        # Save anomalies to database
        saved_anomalies = []
        for anomaly in anomalies:
            # Convert anomaly to database format
            db_anomaly = {
                'log_id': data.get('log_id', 0),
                'device_id': anomaly.get('device_id', 0),
                'type_id': 1,  # Default type
                'score': anomaly.get('confidence', 0.0),
                'is_genuine': True,
                'model_used': ', '.join(anomaly.get('anomaly_type', ['unknown'])),
                'detected_at': anomaly.get('timestamp', None)
            }
            
            # Add to database
            anomaly_id = add_anomaly(db_anomaly)
            if anomaly_id:
                anomaly['id'] = anomaly_id
                saved_anomalies.append(anomaly)
        
        return jsonify({
            'status': 'success',
            'data_processed': True,
            'anomalies_detected': len(anomalies),
            'anomalies_saved': len(saved_anomalies),
            'anomalies': anomalies
        })
    except Exception as e:
        logger.error(f"Error processing anomaly detection: {str(e)}")
        return jsonify({'error': str(e)}), 500

def register_routes(app):
    """Register all API routes with the Flask application"""
    # Register the original API routes
    app.register_blueprint(api_v1)
    
    # Register the generic anomaly detection API endpoints
    app.register_blueprint(generic_detect_bp, url_prefix='/api/v1')
    
    # Log all registered routes
    logger.info("API Routes registered:")
    for rule in app.url_map.iter_rules():
        logger.info(f"  {rule.endpoint:30s} {rule.methods} {rule}")
    
    return app
