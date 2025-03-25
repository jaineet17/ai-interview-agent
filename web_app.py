#!/usr/bin/env python3
import os
import json
import time
import logging
import argparse
import uuid
import mimetypes
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from config import API_HOST, API_PORT

# Import custom components with error handling
try:
    from app import InterviewApp
    from document_processor import DocumentProcessor
    from interview_engine import InterviewEngine, InterviewGenerator
    from interview_engine.llm_adapter import LLMAdapter
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

# Set up CORS to allow Web Speech API to work properly
CORS(app)

# Add mime types for frontend files
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

# Initialize components with error handling
try:
    doc_processor = DocumentProcessor()
    llm_adapter = LLMAdapter()
    interview_generator = InterviewGenerator(llm_adapter)
    
    # Initialize InterviewApp
    interview_app = InterviewApp()
    
    # Session storage
    interview_engines = {}
    
    logger.info("Initializing AI Interview Agent")
except Exception as e:
    logger.error(f"Error initializing components: {e}")
    raise

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
    """Upload a job, company, or candidate document."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Get allowed file extensions
        allowed_extensions = {'.pdf', '.docx', '.txt', '.json'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({
                "error": f"File type not supported. Please upload {', '.join(allowed_extensions)}"
            }), 400
        
        # Save uploaded file
        upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Process document based on type
        processor = DocumentProcessor()
        
        try:
            if doc_type == 'job':
                data = processor.parse_job_post(filepath)
                session['job_data'] = data
                return jsonify({"success": True, "message": "Job data uploaded", "data": data})
            
            elif doc_type == 'company':
                data = processor.parse_company_profile(filepath)
                session['company_data'] = data
                return jsonify({"success": True, "message": "Company data uploaded", "data": data})
            
            elif doc_type == 'candidate':
                data = processor.parse_resume(filepath)
                session['candidate_data'] = data
                return jsonify({"success": True, "message": "Candidate data uploaded", "data": data})
            
            else:
                return jsonify({"error": f"Invalid document type: {doc_type}"}), 400
                
        except Exception as e:
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
def initialize_interview():
    """Initialize the interview engine with job, company, and candidate data."""
    try:
        # Check if we have the necessary data
        if 'job_data' not in session or 'company_data' not in session or 'candidate_data' not in session:
            raise ValueError("Missing required data. Please load data first.")
        
        # Get the session ID
        session_id = str(uuid.uuid4())
        if 'session_id' in session:
            session_id = session['session_id']
        else:
            session['session_id'] = session_id
        
        # Check if demo mode is requested
        data = request.json
        demo_mode = data.get('demo_mode', False) if data else False
        
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
        })

@app.route('/api/start_interview', methods=['POST'])
def start_interview():
    """Start the interview."""
    try:
        # Get the session ID
        session_id = session.get('session_id')
        
        # Check if we have an engine in the session storage
        if not session_id or session_id not in interview_engines:
            # If no initialized interview found, check if we have data to create one
            if 'job_data' not in session or 'company_data' not in session or 'candidate_data' not in session:
                logger.error("No initialized interview and no data to create one")
                return jsonify({
                    'status': 'error',
                    'error': 'No initialized interview found. Please go back to the dashboard and initialize first.'
                })
            
            # We have data, so let's create a new engine
            logger.info("Auto-initializing interview engine from session data")
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
            
            # Create an interview engine instance
            interview_engine = InterviewEngine(
                session['job_data'],
                session['company_data'],
                session['candidate_data'],
                interview_generator
            )
            
            # Generate the interview script
            interview_engine.generate_interview_script()
            
            # Store the engine
            interview_engines[session_id] = interview_engine
        
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
        })

@app.route('/api/process_response', methods=['POST'])
def process_response():
    """Process a response and get the next question."""
    try:
        # Get the request data
        data = request.json
        if not data or 'response' not in data:
            return jsonify({
                'status': 'error',
                'error': 'Missing response data'
            })
        
        response_text = data['response']
        
        # Log the response for debugging
        logger.info(f"Processing response: '{response_text[:50]}{'...' if len(response_text) > 50 else ''}'")
        
        # Get the session ID
        session_id = session.get('session_id')
        if not session_id or session_id not in interview_engines:
            # Try to create a new interview if we have data in session
            if 'job_data' in session and 'company_data' in session and 'candidate_data' in session:
                logger.warning("No active interview session, attempting to create one")
                
                # Create a new session ID
                session_id = str(uuid.uuid4())
                session['session_id'] = session_id
                
                # Create and initialize the interview engine
                interview_engine = InterviewEngine(
                    session['job_data'],
                    session['company_data'],
                    session['candidate_data'],
                    interview_generator
                )
                
                # Generate the interview script and start
                interview_engine.generate_interview_script()
                interview_engine.start_interview()
                interview_engine.interview_active = True
                
                # Store the engine
                interview_engines[session_id] = interview_engine
                
                # Since we just started, instead of processing response,
                # we'll return the first question
                current_q = interview_engine.get_current_question()
                return jsonify({
                    'status': 'success',
                    'message': 'Interview restarted. Please repeat your response.',
                    'question': current_q
                })
            else:
                # No data available to create a new interview
                logger.error("No active interview session and no data to create one")
                return jsonify({
                    'status': 'error',
                    'error': 'No active interview session. Please initialize an interview first.'
                })
        
        # Get the interview engine
        interview_engine = interview_engines[session_id]
        
        # Process the response
        result = interview_engine.process_response(response_text)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing response: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

@app.route('/api/end_interview', methods=['POST'])
def end_interview():
    """End the interview and get the final summary."""
    try:
        # Get the session ID
        session_id = session.get('session_id')
        if not session_id or session_id not in interview_engines:
            raise ValueError("No active interview found.")
        
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
        })

@app.route('/api/visual_summary', methods=['GET'])
def get_visual_summary():
    """Get visual summary data for the interview to display in charts and graphs."""
    try:
        # Get the session ID
        session_id = session.get('session_id')
        
        if not session_id or session_id not in interview_engines:
            return jsonify({
                'status': 'error',
                'error': 'No active interview session found.'
            }), 400
        
        # Get the interview engine
        interview_engine = interview_engines[session_id]
        
        # Check if the interview is complete
        if not interview_engine.interview_complete:
            return jsonify({
                'status': 'error',
                'error': 'Interview is not complete yet. Cannot generate visual summary.'
            }), 400
        
        # Generate the visual summary
        visual_data = interview_engine.generate_visual_summary()
        
        # Get analytics data
        analytics_data = interview_engine.collect_interview_analytics()
        
        # Combine data for frontend
        result = {
            'status': 'success',
            'visual_data': visual_data,
            'analytics': analytics_data
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating visual summary: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': f"Failed to generate visual summary: {str(e)}"
        }), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start the AI Interview Agent web app')
    parser.add_argument('--host', type=str, default=API_HOST, help='Host to run the server on')
    parser.add_argument('--port', type=int, default=API_PORT, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    logger.info(f"Starting AI Interview Agent web app on {args.host}:{args.port}")
    
    app.run(host=args.host, port=args.port, debug=args.debug) 