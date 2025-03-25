# Frontend Integration Guide

This guide outlines how to build and integrate the React frontend with the Flask backend.

## Prerequisites

- Node.js 16+ and npm 8+
- Python 3.8+ with Flask backend running

## Building the Frontend

The React frontend code is located in the `frontend/` directory. To build it for production:

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the production bundle:
   ```bash
   npm run build
   ```

This will create a `dist` directory inside `frontend/` with the compiled assets.

## Configuring the Backend

Ensure the Flask application is properly configured to serve the static files. The code should already include:

```python
app = Flask(__name__, static_folder='frontend/dist')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')
```

## Development Workflow

For development, you can:

1. Run the backend:
   ```bash
   python web_app.py
   ```

2. In a separate terminal, run the frontend in development mode:
   ```bash
   cd frontend
   npm run dev
   ```

This starts a development server with hot reloading at `http://localhost:5173` that proxies API requests to the backend.

## Automatic Build Script

To automate the process, add this script to the project root:

```bash
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
```

Make it executable:
```bash
chmod +x build.sh
```

## Production Deployment Notes

For production deployment:

1. Always run the build script first to ensure the frontend is compiled
2. Consider using a WSGI server like Gunicorn instead of the Flask development server
3. Configure proper CORS headers for security
4. Set up a reverse proxy like Nginx to handle static file serving for better performance

Example production startup:
```bash
gunicorn -w 4 -b 127.0.0.1:8000 "web_app:app"
``` 