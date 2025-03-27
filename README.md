# AI Interview Agent

A state-of-the-art interview simulation system that uses Large Language Models to conduct dynamic, personalized job interviews.

## Overview

The AI Interview Agent is an advanced application that simulates a professional job interview experience. It uses natural language processing and large language models to:

1. Generate personalized interview scripts based on job descriptions and candidate resumes
2. Conduct interactive interviews with natural dialogue flow
3. Provide follow-up questions based on candidate responses
4. Generate comprehensive interview summaries and assessments

Perfect for interview practice, candidate screening, or educational purposes.

## Documentation

For detailed documentation, please refer to the following resources:

- [Main Documentation Hub](DOCUMENTATION.md) - Central reference for all documentation
- [Solution Narrative](SOLUTION_NARRATIVE.md) - Detailed architecture and implementation explanation
- [Frontend Integration Guide](FRONTEND_INTEGRATION.md) - Building and integrating the React frontend
- [Interview Engine Documentation](interview_engine/README.md) - Core interview engine module details

## Features

- **Dynamic Interview Script Generation**: Creates tailored interview questions based on job requirements and candidate background
- **Natural Conversation Flow**: Uses transitions and acknowledgments for a realistic interview experience
- **Intelligent Follow-up Questions**: Adaptively generates relevant follow-ups based on response quality and depth
- **Voice Interface**: Optional speech-to-text and text-to-speech for a hands-free experience
- **Candidate Question Handling**: Detects and responds to questions from the candidate during the interview
- **Duplicate Response Detection**: Identifies repeated answers and prompts for new information
- **Comprehensive Assessment**: Generates detailed interview summaries with strengths, areas for improvement, and recommendations
- **Multi-layer Error Resilience**: Progressive fallback mechanisms for handling LLM failures and malformed outputs
- **Sophisticated JSON Parsing**: Advanced techniques for recovering structured data from imperfect LLM responses
- **Enhanced LLM Service Integration**: Improved health checks and smart fallbacks for service unavailability
- **Demo Mode**: Simplified interview experience with fewer questions for quick testing
- **LLM-based Response Evaluation**: Sophisticated quality assessment of responses beyond simple heuristics
- **Caching System**: Performance optimization through caching of common prompts

## Architecture

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

The system works by:
1. Parsing job and candidate data
2. Generating a structured interview script with questions from different categories
3. Managing the interview flow, including question sequencing and follow-ups
4. Processing candidate responses to determine conversation direction
5. Generating a comprehensive assessment

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Ollama (for local LLM)
- Modern web browser
- Node.js and npm (for frontend development)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jaineet17/ai-interview-agent.git
   cd ai-interview-agent
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables in a `.env` file:
   ```
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=llama3
   FLASK_SECRET_KEY=your_secret_key
   ```

5. Start the web application:
   ```bash
   python web_app.py
   ```

6. Access the application at `http://localhost:8000`

## Usage Guide

1. **Setup Phase**:
   - Click "Load Sample Data" to populate job, company, and candidate information
   - Optionally check "Demo Mode" for a shorter interview
   - Click "Initialize Interview" to generate the interview script
   - Click "Start Interview" to begin

2. **During the Interview**:
   - Read the interviewer's questions and type your responses
   - Use the voice controls (if desired) for speech input/output
   - Ask questions naturally during the interview
   - Provide detailed, relevant answers for the best experience

3. **After the Interview**:
   - Review the AI-generated assessment of your performance
   - Complete the self-assessment section
   - Download or print the summary for your records
   - Start a new interview if desired

## Technical Implementation

- **ConversationMemory**: Maintains context throughout the interview for more natural interactions
- **LLM Integration**: Supports multiple large language models through a flexible adapter pattern
- **Prompt Engineering**: Sophisticated prompt templates for high-quality question generation
- **Response Analysis**: Advanced algorithms for response quality assessment
- **Voice Processing**: Web Speech API integration for voice input and output
- **Responsive Design**: Works on both desktop and mobile devices

## Error Handling & Resilience

The system implements multiple layers of error handling and resilience:

1. **LLM Service Integration**
   - Enhanced health checks for reliable service detection
   - Smart context-aware fallbacks when services are unavailable
   - Properly formatted fallback responses for different request types

2. **JSON Processing Resilience**
   - Multi-stage parsing for handling malformed LLM outputs
   - Regex-based fixes for common issues (missing quotes, colons, brackets)
   - Line-by-line inspection and repair capabilities
   - Structure extraction as a last resort when conventional parsing fails

3. **Interview Flow Continuity**
   - Graceful recovery from errors at every stage of the interview
   - Transparent fallbacks that maintain interview quality
   - State preservation to ensure no data loss during recoveries

## Recent Enhancements

- **Response Quality Evaluation**: Using LLM-based assessment (1-10 scale) instead of simple heuristics
- **Performance Optimization**: Implemented caching for prompts to reduce redundant LLM calls
- **Enhanced Question Detection**: Improved ability to detect when candidates ask questions
- **Multi-layer Error Resilience**: Advanced error handling at every level of the system
- **Robust JSON Parsing**: Sophisticated recovery mechanisms for handling malformed LLM outputs
- **Improved LLM Integration**: Enhanced health checks and smart fallbacks for service unavailability
- **Frontend Improvements**: Better handling of UI states and error conditions

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Mistral AI and Meta for open-source LLMs
- Ollama for the local LLM deployment

## Contact

Project Link: [https://github.com/jaineet17/ai-interview-agent](https://github.com/jaineet17/ai-interview-agent) 