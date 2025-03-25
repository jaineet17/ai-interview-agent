# Interview Engine

The Interview Engine module is responsible for managing the AI-driven interview process, from generating personalized interview scripts to evaluating candidate responses.

## Components

### InterviewEngine

The main class that orchestrates the interview flow, manages questions and responses, and generates interview summaries.

Key features:
- Generate personalized interview scripts based on job, company, and candidate data
- Manage interview flow and question sequencing
- Process candidate responses and generate appropriate follow-up questions
- Generate comprehensive interview summaries with candidate evaluation

### InterviewGenerator

Handles the generation of interview content through LLM interactions.

Key features:
- Generate complete interview scripts with introduction, questions, and closing
- Create follow-up questions based on candidate responses
- Generate comprehensive interview summaries and evaluations

### LLMInterface

Provides a standardized interface for interacting with different language model providers.

Key features:
- Support for multiple LLM providers (OpenAI, Anthropic)
- Standardized text generation API
- Structured JSON response generation

## Usage

### Basic Interview Flow

```python
from interview_engine import InterviewEngine
from interview_engine.interview_generator import InterviewGenerator
from interview_engine.llm_interface import LLMInterface

# Initialize components
llm = LLMInterface(provider="openai", model_name="gpt-4")
generator = InterviewGenerator(llm_interface=llm)

# Prepare data
job_data = {
    "title": "Software Engineer",
    "description": "We're looking for a software engineer with experience in Python...",
    "required_skills": ["Python", "API development", "Database design"]
}

company_data = {
    "name": "Tech Innovations Inc.",
    "description": "A leader in AI-driven software solutions",
    "values": "Innovation, collaboration, quality"
}

candidate_data = {
    "name": "Alex Johnson",
    "experience": "5 years of software development experience",
    "background": "Computer Science degree, worked at startups"
}

# Create interview engine
engine = InterviewEngine(
    job_data=job_data,
    company_data=company_data,
    candidate_data=candidate_data,
    interview_generator=generator
)

# Start the interview
interview_start = engine.start_interview()
print(interview_start["introduction"])
print(f"First question: {interview_start['question']['question']}")

# Process a candidate's response
response = "I have been working with Python for 5 years and have built several APIs..."
next_step = engine.process_response(response)

# Continue with more questions and responses...

# Get the interview summary at the end
if engine.interview_complete:
    summary = engine.summary
    print(f"Recommendation: {summary['recommendation']}")
```

### Configuration

The interview engine components can be configured in various ways:

- **LLM Provider**: Choose between OpenAI and Anthropic for text generation
- **Model Selection**: Specify which model to use (e.g., gpt-4, claude-3-opus)
- **Interview Flow**: Customize the question categories and sequencing

## Dependencies

- Python 3.8+
- Required packages:
  - openai (for OpenAI API)
  - anthropic (for Anthropic API)

## Environment Variables

- `OPENAI_API_KEY`: Required if using OpenAI provider
- `ANTHROPIC_API_KEY`: Required if using Anthropic provider 