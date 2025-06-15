"""
Input Validation Utilities

This module provides functions for validating input data and handling errors
in a consistent way across the application.
"""
import re
import json
import ipaddress
from datetime import datetime
from functools import wraps
from flask import request, jsonify
from utils.logger import get_logger

# Get logger
logger = get_logger()

class ValidationError(Exception):
    """Exception raised for validation errors"""
    def __init__(self, message, field=None, status_code=400):
        self.message = message
        self.field = field
        self.status_code = status_code
        super().__init__(self.message)

def validate_request_json(schema):
    """
    Decorator for validating JSON request data against a schema
    
    Args:
        schema: Dictionary defining the expected schema
               Each key is a field name, and the value is a dictionary with:
               - type: The expected type (str, int, float, bool, list, dict)
               - required: Boolean indicating if the field is required
               - min/max: For numeric types, the min/max allowed value
               - pattern: For string types, a regex pattern to match
               - choices: For any type, a list of allowed values
               - validator: A function that takes the value and returns (is_valid, error_message)
    
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get request data
            data = request.json
            
            # Check if data is None
            if data is None:
                return jsonify({
                    'status': 'error',
                    'message': 'No JSON data provided'
                }), 400
            
            # Validate against schema
            errors = []
            
            for field, rules in schema.items():
                # Check if field is required
                required = rules.get('required', False)
                if required and field not in data:
                    errors.append({
                        'field': field,
                        'message': f"Field '{field}' is required"
                    })
                    continue
                
                # Skip validation if field is not present
                if field not in data:
                    continue
                
                value = data[field]
                
                # Check type
                expected_type = rules.get('type')
                if expected_type:
                    if expected_type == 'str' and not isinstance(value, str):
                        errors.append({
                            'field': field,
                            'message': f"Field '{field}' must be a string"
                        })
                    elif expected_type == 'int' and not isinstance(value, int):
                        errors.append({
                            'field': field,
                            'message': f"Field '{field}' must be an integer"
                        })
                    elif expected_type == 'float' and not isinstance(value, (int, float)):
                        errors.append({
                            'field': field,
                            'message': f"Field '{field}' must be a number"
                        })
                    elif expected_type == 'bool' and not isinstance(value, bool):
                        errors.append({
                            'field': field,
                            'message': f"Field '{field}' must be a boolean"
                        })
                    elif expected_type == 'list' and not isinstance(value, list):
                        errors.append({
                            'field': field,
                            'message': f"Field '{field}' must be an array"
                        })
                    elif expected_type == 'dict' and not isinstance(value, dict):
                        errors.append({
                            'field': field,
                            'message': f"Field '{field}' must be an object"
                        })
                
                # Check min/max for numeric types
                if isinstance(value, (int, float)):
                    if 'min' in rules and value < rules['min']:
                        errors.append({
                            'field': field,
                            'message': f"Field '{field}' must be at least {rules['min']}"
                        })
                    if 'max' in rules and value > rules['max']:
                        errors.append({
                            'field': field,
                            'message': f"Field '{field}' must be at most {rules['max']}"
                        })
                
                # Check pattern for string types
                if isinstance(value, str) and 'pattern' in rules:
                    if not re.match(rules['pattern'], value):
                        errors.append({
                            'field': field,
                            'message': f"Field '{field}' must match pattern: {rules['pattern']}"
                        })
                
                # Check choices for any type
                if 'choices' in rules and value not in rules['choices']:
                    errors.append({
                        'field': field,
                        'message': f"Field '{field}' must be one of: {', '.join(map(str, rules['choices']))}"
                    })
                
                # Check custom validator
                if 'validator' in rules:
                    is_valid, error_message = rules['validator'](value)
                    if not is_valid:
                        errors.append({
                            'field': field,
                            'message': error_message
                        })
            
            # Return errors if any
            if errors:
                return jsonify({
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': errors
                }), 400
            
            # Call the original function
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

def validate_ip_address(value):
    """Validate IP address"""
    try:
        ipaddress.ip_address(value)
        return True, None
    except ValueError:
        return False, f"Invalid IP address: {value}"

def validate_port(value):
    """Validate port number"""
    if not isinstance(value, int):
        return False, "Port must be an integer"
    if value < 1 or value > 65535:
        return False, "Port must be between 1 and 65535"
    return True, None

def validate_timestamp(value, format=None):
    """Validate timestamp"""
    try:
        if format:
            datetime.strptime(value, format)
        else:
            # Try common formats
            for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                try:
                    datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue
            else:
                return False, f"Invalid timestamp format: {value}"
        return True, None
    except ValueError:
        return False, f"Invalid timestamp: {value}"

def validate_json_string(value):
    """Validate JSON string"""
    try:
        json.loads(value)
        return True, None
    except json.JSONDecodeError:
        return False, "Invalid JSON string"

def handle_validation_error(e):
    """Handle ValidationError exceptions"""
    response = {
        'status': 'error',
        'message': str(e.message)
    }
    
    if e.field:
        response['field'] = e.field
    
    return jsonify(response), e.status_code

def setup_error_handlers(app):
    """Set up error handlers for the Flask application"""
    @app.errorhandler(ValidationError)
    def handle_validation_error_app(e):
        return handle_validation_error(e)
    
    @app.errorhandler(400)
    def handle_bad_request(e):
        return jsonify({
            'status': 'error',
            'message': 'Bad request: ' + str(e)
        }), 400
    
    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({
            'status': 'error',
            'message': 'Resource not found: ' + str(e)
        }), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return jsonify({
            'status': 'error',
            'message': 'Method not allowed: ' + str(e)
        }), 405
    
    @app.errorhandler(500)
    def handle_server_error(e):
        logger.error(f"Server error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500
