# AI Interview Agent: Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Descriptions](#component-descriptions)
4. [Setup and Configuration](#setup-and-configuration)
5. [Developer Guide](#developer-guide)
6. [Error Handling](#error-handling)
7. [User Guide](#user-guide)
8. [Recent Improvements](#recent-improvements)
9. [Troubleshooting](#troubleshooting)

## Overview

The AI Interview Agent is a sophisticated application that simulates realistic job interviews using Large Language Models (LLMs). It creates personalized interview experiences by generating questions based on job descriptions and candidate profiles, maintaining natural conversational flow, and providing detailed feedback.

## System Architecture

The system follows a modular architecture:

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

## Component Descriptions

### Interview Engine

The core interview engine manages the entire interview flow including:
- Question generation and sequencing
- Response analysis and follow-up determination
- Conversation memory and context tracking
- Summary and assessment generation

### Document Processor

Handles parsing and information extraction from:
- Job descriptions
- Company profiles
- Candidate resumes

### Frontend

React-based user interface with:
- Dashboard for setup and initialization
- Interview interface with chat and voice controls
- Summary view with assessment and visualization

## Setup and Configuration

### Prerequisites
- Python 3.8+
- Node.js and npm
- Ollama or other LLM provider

### Installation Steps

1. Clone the repository
2. Set up a Python virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Configure environment variables in `.env`
5. Start the application: `python web_app.py`

### Environment Variables

```
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3
FLASK_SECRET_KEY=your_secret_key
```

## Developer Guide

### Development Environment

For development with hot reloading:

```bash
# Start development servers with hot reloading
./start-dev.sh
```

This script will:
1. Start the Flask backend with auto-reload
2. Run the Vite development server with HMR
3. Monitor both for changes

### Code Structure

- **Frontend**: React with TypeScript and Material UI
- **Backend**: Flask API with Blueprints
- **Interview Engine**: Core Python modules

### Building the Frontend

```bash
cd frontend
npm run build
```

## Error Handling

The system implements comprehensive error handling:

### Backend Error Handling
- **Multi-layer validation** in data processing
- **Try/except blocks** around critical operations
- **Fallback responses** for error scenarios
- **Defensive programming** with default values

### Frontend Error Handling
- **Optional chaining** for accessing nested properties
- **Conditional rendering** based on data availability
- **Type validation** before rendering complex objects
- **Fallback UI components** when data is missing

### Visualization Error Handling
- **Data structure validation** before rendering charts
- **Default values** for missing properties
- **Truncation handling** for text overflow
- **Tooltip fallbacks** for inaccessible content

## User Guide

### Starting an Interview
1. Upload or select sample job, company, and candidate data
2. Initialize the interview
3. Start the interview session

### During the Interview
1. Read questions from the AI interviewer
2. Type responses or use voice input
3. Ask questions naturally during your responses

### After the Interview
1. Review the AI-generated assessment
2. Explore the visual analytics dashboard
3. Download or share your results

## Recent Improvements

### Visual Analytics Enhancement
The visual summary dashboard has been completely redesigned for better readability and professionalism:
- **Improved Text Handling**: Truncation with tooltips for long text
- **Better Layout**: Increased margins and spacing for readability
- **Enhanced Charts**: Rounded corners, better animations, and responsive design
- **Professional Styling**: Color harmonization and consistent typography

### Error Resilience
Multiple layers of error handling have been implemented:
- **Defensive Object Processing**: Robust handling of various data structures
- **Speech Synthesis Improvements**: Better error management for voice controls
- **Comprehensive Validation**: Type checking and fallback mechanisms
- **Graceful Degradation**: Sensible defaults when data is missing or malformed

### Development Experience
Enhanced developer workflow with:
- **Hot Module Replacement**: Frontend changes reflect instantly
- **Flask Auto-Reload**: Backend changes apply automatically
- **Unified Development Script**: Single command to start both servers
- **Better Error Reporting**: More descriptive error messages

### React Component Upgrades
- **Advanced State Management**: Better handling of loading and error states
- **Type-Safe Interfaces**: Enhanced TypeScript interfaces for complex objects
- **Conditional Rendering**: Improved handling of missing or malformed data
- **Accessibility Improvements**: Better screen reader support and keyboard navigation

## Troubleshooting

### Common Issues

#### Speech Recognition Not Working
- Ensure your browser supports the Web Speech API
- Check microphone permissions
- Try a different browser (Chrome works best)

#### Visual Summary Errors
- Ensure the interview is fully completed
- Check the console for specific error messages
- Verify LLM connectivity for summary generation

#### LLM Connection Issues
- Verify Ollama is running (or your chosen LLM provider)
- Check network connectivity
- Ensure your API keys are correctly configured

### Getting Help

For additional assistance:
- Check the [GitHub Issues](https://github.com/jaineet17/ai-interview-agent/issues)
- Review the [Solution Narrative](SOLUTION_NARRATIVE.md) for detailed implementation explanations
- Contact the project maintainers through GitHub 