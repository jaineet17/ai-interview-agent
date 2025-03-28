#!/usr/bin/env python3
"""
Development server with hot reloading for the AI Interview Agent.
This script automatically reloads the Flask app when changes are detected.
"""
import os
import sys
import logging
from web_app import app, API_HOST, API_PORT

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO,
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('dev-server')
    
    # Enable hot reloading
    logger.info("Starting development server with hot reloading enabled")
    
    # Check if watchdog is installed
    try:
        import watchdog
    except ImportError:
        logger.warning("Watchdog not installed. For better hot reloading, install with: pip install watchdog")
    
    # Set up Flask development server with hot reloading
    app.config['DEBUG'] = True  # Enable debug mode
    app.config['TEMPLATES_AUTO_RELOAD'] = True  # Auto-reload templates
    app.jinja_env.auto_reload = True  # Auto-reload Jinja templates
    
    # Run with hot reloading enabled
    logger.info(f"Starting server on {API_HOST}:{API_PORT}")
    app.run(
        host=API_HOST,
        port=API_PORT,
        debug=True,  # Enable debug mode
        use_reloader=True,  # Enable hot reloading
        threaded=True,  # Enable threading
        extra_files=[  # Watch additional files
            'frontend/dist/index.html',
            'frontend/dist/assets',
        ]
    ) 