from functools import wraps
from flask import request, jsonify, session
from datetime import datetime

# These will be imported from web_app.py
session_lock = None
SESSION_TIMEOUT = None
interview_engines = None
session_last_access = None

def set_session_globals(lock, timeout, engines, last_access):
    """Set the session globals from web_app.py"""
    global session_lock, SESSION_TIMEOUT, interview_engines, session_last_access
    session_lock = lock
    SESSION_TIMEOUT = timeout
    interview_engines = engines
    session_last_access = last_access

# Input validation decorators
def validate_json(*required_fields):
    """Decorator to validate JSON payload and required fields"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if request has JSON content
            if not request.is_json:
                return jsonify({"error": "Request must be JSON"}), 400
            
            # Get JSON data
            data = request.get_json()
            if data is None:
                return jsonify({"error": "Invalid JSON format"}), 400
            
            # Check for required fields
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400
            
            # Check for empty fields
            empty_fields = [field for field in required_fields if not data.get(field) and data.get(field) is not None]
            if empty_fields:
                return jsonify({
                    "error": f"Empty required fields: {', '.join(empty_fields)}"
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_session(f):
    """Decorator to validate session existence and expiry"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({
                "status": "error", 
                "error": "No active session. Please initialize an interview."
            }), 401
        
        # Check if session exists in our session storage
        with session_lock:
            if session_id not in session_last_access:
                return jsonify({
                    "status": "error",
                    "error": "Session not found. It may have expired."
                }), 401
            
            current_time = datetime.now()
            last_access = session_last_access[session_id]
            
            if (current_time - last_access).total_seconds() > SESSION_TIMEOUT:
                # Session has expired
                if session_id in interview_engines:
                    del interview_engines[session_id]
                del session_last_access[session_id]
                return jsonify({
                    "status": "session_expired",
                    "error": "Your session has expired. Please refresh and start a new interview."
                }), 401
            
            # Update last access time
            session_last_access[session_id] = current_time
        
        return f(*args, **kwargs)
    return decorated_function 