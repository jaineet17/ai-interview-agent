import logging
import sys
from pathlib import Path
from config import LOG_DIR, ENVIRONMENT

# Create LOG_DIR if it doesn't exist
LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging():
    """Set up logging configuration."""
    # Configure logging
    log_file = LOG_DIR / "interview_agent.log"
    
    # Set up handler
    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Set level based on environment
    log_level = logging.DEBUG if ENVIRONMENT == "development" else logging.INFO
    
    # Configure format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logging.info("Logging initialized")

# Set up handler
file_handler = logging.FileHandler(LOG_DIR / "interview_agent.log")
console_handler = logging.StreamHandler(sys.stdout)

# Set level based on environment
log_level = logging.DEBUG if ENVIRONMENT == "development" else logging.INFO

# Configure format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Set up root logger
root_logger = logging.getLogger()
root_logger.setLevel(log_level)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

def get_logger(name):
    """Get a logger with the specified name."""
    return logging.getLogger(name) 