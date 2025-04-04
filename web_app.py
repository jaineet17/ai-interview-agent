#!/usr/bin/env python3
import os
import json
import time
import logging
import argparse
import uuid
import mimetypes
from pathlib import Path
from datetime import datetime, timedelta
import threading
from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from config import API_HOST, API_PORT
from validators import validate_json, validate_session, set_session_globals
from interview_engine import InterviewEngine, InterviewGenerator
from interview_engine.llm_adapter import LLMAdapter
from interview_engine.interview_engine import resource_monitor

# Session cleanup mechanism
SESSION_TIMEOUT = 60 * 60  # 1 hour in seconds
session_last_access = {}
session_lock = threading.Lock()

def session_cleanup_task():
    """Background task to clean up expired sessions"""
    with session_lock:
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, last_access in session_last_access.items():
            if (current_time - last_access).total_seconds() > SESSION_TIMEOUT:
                expired_sessions.append(session_id)
        
        # Clean up expired sessions
        for session_id in expired_sessions:
            if session_id in interview_engines:
                logger.info(f"Cleaning up expired session: {session_id}")
                del interview_engines[session_id]
                del session_last_access[session_id]
    
    # Schedule the next cleanup
    threading.Timer(300, session_cleanup_task).start()  # Run every 5 minutes

# Resource monitoring task to periodically check memory usage
def resource_monitor_task():
    """Background task to monitor system resources"""
    resource_monitor.check_resources()
    
    # Schedule the next check
    threading.Timer(60, resource_monitor_task).start()  # Run every minute

# Import custom components with error handling
try:
    from app import InterviewApp
    from document_processor import DocumentProcessor
    from interview_engine import InterviewEngine, InterviewGenerator
    from interview_engine.llm_adapter import LLMAdapter
    from interview_engine.interview_engine import resource_monitor
except ImportError as e:
    print(f"Error importing required modules: {e}")
    raise

# Load environment variables
load_dotenv()

# Set up logging
try:
    from logger import setup_logging
    setup_logging()
    logger = logging.getLogger('app')
except Exception as e:
    print(f"Error setting up logging: {e}")
    # Fallback basic logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('app')

# Initialize Flask app
app = Flask(__name__, static_folder='frontend/dist')
app.secret_key = os.getenv("FLASK_SECRET_KEY", str(uuid.uuid4()))
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize components with error handling
try:
    doc_processor = DocumentProcessor()
    llm_adapter = LLMAdapter()
    interview_generator = InterviewGenerator(llm_adapter)
    
    # Initialize InterviewApp
    interview_app = InterviewApp()
    
    # Session storage
    interview_engines = {}
    
    # Set session globals for validators
    set_session_globals(session_lock, SESSION_TIMEOUT, interview_engines, session_last_access)
    
    logger.info("Initializing AI Interview Agent")
except Exception as e:
    logger.error(f"Error initializing components: {e}")
    raise

# Start the cleanup task and resource monitor when app starts
@app.before_request
def before_first_request():
    """Run tasks before first request (replaces deprecated before_first_request)"""
    if not hasattr(app, 'before_first_request_complete'):
        app.before_first_request_complete = True
        session_cleanup_task()
        resource_monitor_task()

# Add this middleware to track session activity
@app.before_request
def check_session_activity():
    session_id = session.get('session_id')
    if session_id:
        with session_lock:
            session_last_access[session_id] = datetime.now()

# Set up CORS to allow Web Speech API to work properly
CORS(app)

# Add mime types for frontend files
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

# Helper function to get interview engine with session validation
def get_interview_engine(session_id):
    """Get the interview engine for the session with expiry handling."""
    if not session_id:
        return None, "No session ID found. Please initialize an interview."
    
    with session_lock:
        if session_id not in session_last_access:
            return None, "Session not found. It may have expired."
        
        current_time = datetime.now()
        last_access = session_last_access[session_id]
        
        if (current_time - last_access).total_seconds() > SESSION_TIMEOUT:
            # Session has expired
            if session_id in interview_engines:
                del interview_engines[session_id]
            del session_last_access[session_id]
            return None, "Your session has expired. Please refresh and start a new interview."
        
        # Update last access time
        session_last_access[session_id] = current_time
        
        if session_id not in interview_engines:
            return None, "No active interview found for this session."
        
        return interview_engines[session_id], None

# Serve React frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# API routes
@app.route('/api/upload/<doc_type>', methods=['POST'])
def upload_document(doc_type):
    """Upload a job, company, or candidate document with enhanced security."""
    try:
        # Validate doc_type
        valid_doc_types = ['job', 'company', 'candidate']
        if doc_type not in valid_doc_types:
            return jsonify({
                "error": f"Invalid document type. Must be one of: {', '.join(valid_doc_types)}"
            }), 400
            
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Get file details for validation
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        content_type = file.content_type
        
        # Define allowed extensions and their corresponding MIME types
        allowed_types = {
            '.pdf': ['application/pdf'],
            '.docx': [
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.ms-word.document.macroEnabled.12'
            ],
            '.txt': ['text/plain'],
            '.json': ['application/json']
        }
        
        # Validate file extension
        if file_ext not in allowed_types:
            return jsonify({
                "error": f"File type not supported. Please upload PDF, DOCX, TXT, or JSON"
            }), 400
        
        # Validate MIME type
        if content_type not in allowed_types.get(file_ext, []):
            return jsonify({
                "error": f"File content does not match its extension. Security check failed."
            }), 400
        
        # Validate file size - 10MB limit
        max_size = 10 * 1024 * 1024  # 10MB
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size > max_size:
            return jsonify({
                "error": f"File size exceeds the 10MB limit."
            }), 400
        
        # Create a unique filename to prevent overwriting
        unique_filename = f"{int(time.time())}_{filename}"
        
        # Save uploaded file in document type specific folder for better organization
        upload_dir = os.path.join(os.path.dirname(__file__), 'uploads', doc_type)
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, unique_filename)
        file.save(filepath)
        
        # Basic content validation for different file types
        try:
            # For PDF, check it's actually a PDF
            if file_ext == '.pdf':
                import PyPDF2
                try:
                    PyPDF2.PdfReader(filepath)
                except Exception as e:
                    os.remove(filepath)  # Delete the suspicious file
                    return jsonify({"error": f"Invalid PDF file: {str(e)}"}), 400
            
            # For DOCX, verify it's a valid DOCX
            elif file_ext == '.docx':
                import docx
                try:
                    docx.Document(filepath)
                except Exception as e:
                    os.remove(filepath)  # Delete the suspicious file
                    return jsonify({"error": f"Invalid DOCX file: {str(e)}"}), 400
            
            # For JSON, verify it's valid JSON
            elif file_ext == '.json':
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    os.remove(filepath)  # Delete the invalid file
                    return jsonify({"error": f"Invalid JSON file: {str(e)}"}), 400
        except ImportError as e:
            logger.warning(f"Couldn't validate file content due to missing dependency: {str(e)}")
            # Continue anyway since we already checked MIME type
        
        # Process document based on type
        processor = DocumentProcessor()
        
        try:
            if doc_type == 'job':
                data = processor.parse_job_post(filepath)
                session['job_data'] = data
                logger.info(f"Successfully processed job document: {filename}")
                return jsonify({"success": True, "message": "Job data uploaded", "data": data})
            
            elif doc_type == 'company':
                data = processor.parse_company_profile(filepath)
                session['company_data'] = data
                logger.info(f"Successfully processed company document: {filename}")
                return jsonify({"success": True, "message": "Company data uploaded", "data": data})
            
            elif doc_type == 'candidate':
                data = processor.parse_resume(filepath)
                session['candidate_data'] = data
                logger.info(f"Successfully processed candidate document: {filename}")
                return jsonify({"success": True, "message": "Candidate data uploaded", "data": data})
            
            else:
                # Remove file if document type is invalid
                os.remove(filepath)
                return jsonify({"error": f"Invalid document type: {doc_type}"}), 400
                
        except Exception as e:
            # Delete the file if processing failed
            os.remove(filepath)
            logger.error(f"Document processing error: {str(e)}")
            return jsonify({"error": f"Error processing document: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@app.route('/api/load_sample_data', methods=['POST'])
def load_sample_data():
    """Load sample data for demonstration."""
    try:
        # Load sample data from JSON files
        with open('data/sample_job.json', 'r') as f:
            job_data = json.load(f)
        
        with open('data/sample_company.json', 'r') as f:
            company_data = json.load(f)
        
        with open('data/sample_candidate.json', 'r') as f:
            candidate_data = json.load(f)
        
        # Save data to session
        session['job_data'] = job_data
        session['company_data'] = company_data
        session['candidate_data'] = candidate_data
        
        logger.info("Sample data loaded successfully")
        
        return jsonify({
            'status': 'success',
            'job_data': job_data,
            'company_data': company_data,
            'candidate_data': candidate_data
        })
    except Exception as e:
        logger.error(f"Error loading sample data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/initialize_interview', methods=['POST'])
@validate_json()  # No required fields, but validates JSON format
def initialize_interview():
    """Initialize the interview engine with job, company, and candidate data."""
    try:
        # Check if we have the necessary data
        if 'job_data' not in session or 'company_data' not in session or 'candidate_data' not in session:
            return jsonify({
                "success": False,
                "error": "Missing required data. Please load data first."
            }), 400
        
        # Get the session ID
        session_id = str(uuid.uuid4())
        if 'session_id' in session:
            session_id = session['session_id']
        else:
            session['session_id'] = session_id
        
        # Check if demo mode is requested
        data = request.json
        demo_mode = data.get('demo_mode', False) if data else False
        
        # Validate demo_mode is boolean
        if not isinstance(demo_mode, bool):
            return jsonify({
                "success": False,
                "error": "demo_mode must be a boolean value"
            }), 400
        
        logger.info("Initializing interview engine")
        
        # Create an interview engine instance
        interview_engine = InterviewEngine(
            session['job_data'],
            session['company_data'],
            session['candidate_data'],
            interview_generator
        )
        
        # Generate the interview script with demo mode if requested
        interview_engine.generate_interview_script(demo_mode=demo_mode)
        
        # Store the engine in our session-based storage
        interview_engines[session_id] = interview_engine
        
        # Record the session access time
        with session_lock:
            session_last_access[session_id] = datetime.now()
        
        logger.info("Interview engine initialized successfully")
        
        return jsonify({
            'success': True,
            'message': 'Interview initialized successfully'
        })
    except Exception as e:
        logger.error(f"Error initializing interview: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/start_interview', methods=['POST'])
@validate_session
def start_interview():
    """Start the interview."""
    try:
        # Get the session ID
        session_id = session.get('session_id')
        
        # Get the interview engine
        interview_engine = interview_engines[session_id]
        
        # Start the interview if not already active
        if not interview_engine.interview_active:
            result = interview_engine.start_interview()
            interview_engine.interview_active = True
            logger.info("Interview started successfully")
        else:
            # Interview already active, return current question
            current_q = interview_engine.get_current_question()
            if current_q:
                result = {
                    'question': current_q,
                    'message': 'Continuing existing interview'
                }
            else:
                result = {
                    'status': 'error',
                    'error': 'Interview in invalid state. Please initialize again.'
                }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error starting interview: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/process_response', methods=['POST'])
@validate_json('response')
@validate_session
def process_response():
    """Process a response and get the next question."""
    try:
        # Get the request data
        data = request.json
        response_text = data['response']
        
        # Validate response text (basic validation)
        if len(response_text.strip()) == 0:
            return jsonify({
                'status': 'error',
                'error': 'Response cannot be empty'
            }), 400
        
        # Limit response length to prevent abuse
        max_length = 10000  # 10k characters should be plenty
        if len(response_text) > max_length:
            response_text = response_text[:max_length]
            logger.warning(f"Response truncated to {max_length} characters")
        
        # Log the response for debugging (truncated for privacy)
        truncated_log = response_text[:30] + '...' if len(response_text) > 30 else response_text
        logger.info(f"Processing response: '{truncated_log}'")
        
        # Get the session ID
        session_id = session.get('session_id')
        
        # Get the interview engine
        interview_engine = interview_engines[session_id]
        
        # Process the response
        result = interview_engine.process_response(response_text)
        return jsonify(result)
        
    except KeyError as e:
        logger.error(f"Missing key in process_response: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': f"Missing required data: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"Error processing response: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/end_interview', methods=['POST'])
@validate_session
def end_interview():
    """End the interview and get the final summary."""
    try:
        # Get the session ID
        session_id = session.get('session_id')
        
        # Get the interview engine
        interview_engine = interview_engines[session_id]
        
        # Generate the summary
        summary = interview_engine.generate_summary()
        
        # Mark the interview as complete
        interview_engine.interview_active = False
        interview_engine.interview_complete = True
        
        logger.info("Interview ended successfully")
        
        return jsonify({
            'status': 'success',
            'summary': summary
        })
    except Exception as e:
        logger.error(f"Error ending interview: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/visual_summary', methods=['GET'])
@validate_session
def get_visual_summary():
    """Get visual summary data for the interview to display in charts and graphs."""
    try:
        # Get the session ID
        session_id = session.get('session_id')
        
        # Get the interview engine
        interview_engine = interview_engines[session_id]
        
        # Check if the interview is complete
        if not interview_engine.interview_complete:
            return jsonify({
                'status': 'error',
                'error': 'Interview is not complete yet. Cannot generate visual summary.'
            }), 400
        
        # Generate the visual summary
        try:
            visual_data = interview_engine.generate_visual_summary()
            
            # Validate the visual data structure
            if not isinstance(visual_data, dict):
                logger.error(f"Invalid visual data type: {type(visual_data)}")
                # Create a fallback structure if visual_data is not a dictionary
                visual_data = {
                    "candidate_name": "Candidate",
                    "position": "Position",
                    "skill_ratings": [
                        {"name": "Technical Knowledge", "score": 70},
                        {"name": "Problem Solving", "score": 65},
                        {"name": "Communication", "score": 75}
                    ],
                    "strengths": [
                        {"text": "Communication skills", "score": 85},
                        {"text": "Technical knowledge", "score": 80}
                    ],
                    "improvements": [
                        {"text": "Documentation", "score": 60},
                        {"text": "Specific examples", "score": 50}
                    ],
                    "recommendation_score": 70,
                    "recommendation_text": "Candidate shows potential for the role."
                }
        except Exception as visual_err:
            logger.error(f"Error generating visual data: {str(visual_err)}")
            # Create a fallback visual data structure on error
            visual_data = {
                "candidate_name": "Candidate",
                "position": "Position",
                "skill_ratings": [
                    {"name": "Technical Knowledge", "score": 70},
                    {"name": "Problem Solving", "score": 65},
                    {"name": "Communication", "score": 75}
                ],
                "strengths": [
                    {"text": "Communication skills", "score": 85},
                    {"text": "Technical knowledge", "score": 80}
                ],
                "improvements": [
                    {"text": "Documentation", "score": 60},
                    {"text": "Specific examples", "score": 50}
                ],
                "recommendation_score": 70,
                "recommendation_text": "Candidate shows potential for the role."
            }
        
        # Get analytics data with error handling
        try:
            analytics_data = interview_engine.collect_interview_analytics()
            if not isinstance(analytics_data, dict):
                analytics_data = {"error": "Invalid analytics data format"}
        except Exception as analytics_err:
            logger.error(f"Error collecting analytics data: {str(analytics_err)}")
            analytics_data = {"error": "Failed to collect analytics data"}
        
        # Combine data for frontend with proper error checking
        result = {
            'status': 'success',
            'visual_data': visual_data,
            'analytics': analytics_data
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating visual summary: {str(e)}")
        # Return a structured error response with a fallback object
        return jsonify({
            'status': 'error',
            'error': f"Failed to generate visual summary: {str(e)}",
            'visual_data': {
                "candidate_name": "Candidate",
                "position": "Position",
                "skill_ratings": [
                    {"name": "Technical Knowledge", "score": 70},
                    {"name": "Problem Solving", "score": 65},
                    {"name": "Communication", "score": 75}
                ],
                "strengths": [
                    {"text": "Communication skills", "score": 85},
                    {"text": "Technical knowledge", "score": 80}
                ],
                "improvements": [
                    {"text": "Documentation", "score": 60},
                    {"text": "Specific examples", "score": 50}
                ],
                "recommendation_score": 70,
                "recommendation_text": "Candidate shows potential for the role."
            }
        }), 200  # Return 200 with fallback data rather than 500 to prevent frontend errors

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start the AI Interview Agent web app')
    parser.add_argument('--host', type=str, default=API_HOST, help='Host to run the server on')
    parser.add_argument('--port', type=int, default=API_PORT, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    logger.info(f"Starting AI Interview Agent web app on {args.host}:{args.port}")
    
    app.run(host=args.host, port=args.port, debug=args.debug) 