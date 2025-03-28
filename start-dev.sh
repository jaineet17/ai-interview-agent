#!/bin/bash

# Start development environment with hot reloading for AI Interview Agent
echo "Starting AI Interview Agent development environment with hot reloading..."

# Check if required tools are installed
if ! command -v python3 &> /dev/null
then
    echo "Python 3 could not be found. Please install Python 3."
    exit 1
fi

if ! command -v npm &> /dev/null
then
    echo "npm could not be found. Please install Node.js and npm."
    exit 1
fi

# Install watchdog for better Flask hot reloading if not already installed
pip install watchdog

# Install concurrently if not already installed
if ! command -v concurrently &> /dev/null
then
    echo "Installing concurrently..."
    npm install -g concurrently
fi

# Start both frontend and backend in development mode
echo "Starting development servers..."
concurrently \
  --names "BACKEND,FRONTEND" \
  --prefix-colors "blue.bold,green.bold" \
  --kill-others \
  "python3 dev.py" \
  "cd frontend && npm run dev:hot"

# If concurrently is not available, use this as a fallback
# echo "Starting backend development server..."
# python3 dev.py &
# BACKEND_PID=$!
# echo "Starting frontend development server..."
# cd frontend && npm run dev:hot &
# FRONTEND_PID=$!
# 
# # Handle cleanup when script is terminated
# trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM EXIT
# 
# # Wait for both processes
# wait 