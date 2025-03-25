# AI Interview Agent Documentation

This document serves as the central hub for all documentation related to the AI Interview Agent. It provides links to all specialized documentation and offers a comprehensive overview of the system.

## Documentation Overview

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Main project overview, features, and quick start |
| [Solution Narrative](SOLUTION_NARRATIVE.md) | Detailed explanation of the solution architecture and implementation |
| [Frontend Integration](FRONTEND_INTEGRATION.md) | Guide for building and integrating the React frontend |
| [Interview Engine](interview_engine/README.md) | Documentation for the core interview engine module |

## System Architecture

The AI Interview Agent is structured as follows:

```
AI Interview Agent
├── interview_engine/            # Core interview functionality
│   ├── interview_engine.py      # Main interview flow controller
│   ├── interview_generator.py   # Question generation and prompting
│   ├── llm_interface.py         # LLM provider abstraction
│   └── llm_adapter.py           # Adapter for multiple LLM providers
├── document_processor/          # Document parsing and information extraction
├── frontend/                    # React-based UI
│   ├── src/                     # React components and pages
│   ├── public/                  # Static assets
├── llm_service/                 # LLM integration services
├── data/                        # Data storage
├── app.py                       # API controller
├── web_app.py                   # Web application launcher
└── requirements.txt             # Python dependencies
```

## Quick Installation

```bash
# Clone the repository
git clone https://github.com/jaineet17/ai-interview-agent.git
cd ai-interview-agent

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Build the frontend
bash build.sh

# Run the application
python web_app.py
```

## Core Components

### Interview Engine

The heart of the system that manages interview flow. See [Interview Engine Documentation](interview_engine/README.md) for details.

### Document Processor

Handles parsing and extracting information from:
- Job descriptions
- Company profiles
- Candidate resumes

### Frontend

React-based interface with:
- Dashboard for document upload
- Interview interface with voice capabilities
- Summary and assessment view

See [Frontend Integration Guide](FRONTEND_INTEGRATION.md) for building and development instructions.

### Web Application

Flask-based backend API that:
- Serves the frontend
- Manages API endpoints
- Handles session management
- Processes file uploads

## Common Tasks

### Setting Up for Development

1. Follow the installation instructions above
2. For frontend development, run:
   ```bash
   cd frontend
   npm run dev
   ```
3. In a separate terminal, run the backend:
   ```bash
   python web_app.py
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_interview_engine.py
```

### Deploying to Production

See the [Frontend Integration Guide](FRONTEND_INTEGRATION.md) for production deployment instructions.

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3
FLASK_SECRET_KEY=your_secret_key
```

### LLM Configuration

The system supports multiple LLM providers:
- OpenAI: Requires `OPENAI_API_KEY`
- Anthropic: Requires `ANTHROPIC_API_KEY`
- Ollama: Requires `OLLAMA_API_BASE` (default: http://localhost:11434)

## Troubleshooting

### Common Issues

1. **No frontend content displayed**: Make sure to build the frontend using the build.sh script
2. **LLM connection errors**: Check if the configured LLM provider is accessible
3. **Session expiry issues**: Check the session timeout configuration in web_app.py

## Contributing

To contribute to the project:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 