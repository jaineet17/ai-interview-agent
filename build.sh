#!/bin/bash
# build.sh - Build script for AI Interview Agent

echo "Building AI Interview Agent..."

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install Node.js and npm."
    exit 1
fi

# Build frontend
echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Build complete. You can now run the application with:"
echo "python web_app.py" 