"""
Feedback API Routes

This module provides API endpoints for managing feedback on anomaly detections
and controlling the feedback-based model retraining process.
"""
from flask import Blueprint, jsonify, request
from ml.feedback_loop import record_anomaly_feedback, force_model_retrain, get_feedback_statistics
from utils.logger import get_logger
from utils.validation import validate_request_json, ValidationError

# Get logger
logger = get_logger()

# Create blueprint
feedback_bp = Blueprint('feedback', __name__, url_prefix='/api/v1/feedback')

@feedback_bp.route('/status', methods=['GET'])
def get_status():
    """Get feedback statistics and status"""
    stats = get_feedback_statistics()
    return jsonify(stats)

@feedback_bp.route('/submit', methods=['POST'])
@validate_request_json({
    'anomaly_id': {
        'type': 'int',
        'required': True,
        'min': 1
    },
    'is_genuine': {
        'type': 'bool',
        'required': True
    },
    'comment': {
        'type': 'str',
        'required': False
    }
})
def submit_feedback():
    """Submit feedback for an anomaly detection"""
    data = request.json
    
    try:
        # Record feedback
        success = record_anomaly_feedback(data['anomaly_id'], data['is_genuine'])
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f"Feedback recorded for anomaly {data['anomaly_id']}"
            })
        else:
            # Raise a validation error if feedback recording fails
            raise ValidationError(
                f"Failed to record feedback for anomaly {data['anomaly_id']}", 
                status_code=500
            )
    
    except Exception as e:
        # Log the error
        logger.error(f"Error submitting feedback: {str(e)}")
        
        # Return error response
        return jsonify({
            'status': 'error',
            'message': f"Failed to record feedback for anomaly {data['anomaly_id']}: {str(e)}"
        }), 500

@feedback_bp.route('/retrain', methods=['POST'])
def retrain_models():
    """Force retraining of anomaly detection models"""
    success = force_model_retrain()
    
    if success:
        return jsonify({
            'status': 'success',
            'message': 'Models retrained successfully'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrain models'
        }), 500
