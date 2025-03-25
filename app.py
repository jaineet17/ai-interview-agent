#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

from config import DATA_DIR, UPLOAD_DIR
from logger import get_logger
from document_processor import DocumentProcessor
from interview_engine import InterviewEngine, InterviewGenerator
from interview_engine.llm_adapter import LLMAdapter
from llm_service import LLMService

# Set up logging
logger = get_logger(__name__)

class InterviewApp:
    """Main application for the AI Interview Agent."""
    
    def __init__(self):
        """Initialize the application components."""
        logger.info("Initializing AI Interview Agent")
        
        # Initialize the document processor
        self.doc_processor = DocumentProcessor()
        
        # Initialize the LLM adapter
        self.llm_adapter = LLMAdapter()
        
        # Initialize the interview generator with the LLM adapter
        self.interview_generator = InterviewGenerator(self.llm_adapter)
        
        # Interview engine will be initialized when needed
        self.interview_engine = None
        
        # Data
        self.job_data = {}
        self.company_data = {}
        self.candidate_data = {}
        
        # Ensure data directories exist
        (DATA_DIR / "interviews").mkdir(exist_ok=True)
        (DATA_DIR / "processed").mkdir(exist_ok=True)
    
    def process_documents(self, job_file: str, company_file: str, resume_file: str) -> bool:
        """Process the input documents to extract structured data."""
        logger.info(f"Processing documents: job={job_file}, company={company_file}, resume={resume_file}")
        
        try:
            # Process job description
            if job_file:
                self.job_data = self.doc_processor.parse_job_post(job_file)
                logger.info(f"Processed job data: {self.job_data.get('title', 'Unknown')}")
            
            # Process company profile
            if company_file:
                self.company_data = self.doc_processor.parse_company_profile(company_file)
                logger.info(f"Processed company data: {self.company_data.get('name', 'Unknown')}")
            
            # Process candidate resume
            if resume_file:
                self.candidate_data = self.doc_processor.parse_resume(resume_file)
                logger.info(f"Processed candidate data: {self.candidate_data.get('name', 'Unknown')}")
            
            # Save processed data for future use
            self._save_processed_data()
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing documents: {str(e)}")
            return False
    
    def _save_processed_data(self) -> None:
        """Save the processed data to JSON files."""
        timestamp = int(os.path.getmtime(UPLOAD_DIR)) if os.path.exists(UPLOAD_DIR) else int(time.time())
        
        # Save job data
        if self.job_data:
            with open(DATA_DIR / "processed" / f"job_data_{timestamp}.json", "w") as f:
                json.dump(self.job_data, f, indent=2)
        
        # Save company data
        if self.company_data:
            with open(DATA_DIR / "processed" / f"company_data_{timestamp}.json", "w") as f:
                json.dump(self.company_data, f, indent=2)
        
        # Save candidate data
        if self.candidate_data:
            with open(DATA_DIR / "processed" / f"candidate_data_{timestamp}.json", "w") as f:
                json.dump(self.candidate_data, f, indent=2)
    
    def initialize_interview(self) -> Dict[str, Any]:
        """Initialize the interview engine and generate a script."""
        if not all([self.job_data, self.company_data, self.candidate_data]):
            logger.error("Missing required data for interview initialization")
            return {"error": "Missing job, company, or candidate data. Please process documents first."}
        
        logger.info("Initializing interview engine")
        
        try:
            # Initialize interview engine with the processed data
            self.interview_engine = InterviewEngine(
                job_data=self.job_data,
                company_data=self.company_data,
                candidate_data=self.candidate_data,
                interview_generator=self.interview_generator
            )
            
            # Generate the interview script
            self.interview_engine.generate_interview_script()
            
            logger.info("Interview engine initialized successfully")
            return {"success": True, "message": "Interview engine initialized successfully"}
            
        except Exception as e:
            logger.error(f"Error initializing interview: {str(e)}")
            return {"error": f"Failed to initialize interview: {str(e)}"}
    
    def start_interview(self) -> Dict[str, Any]:
        """Start the interview process."""
        if not self.interview_engine:
            logger.error("Interview engine not initialized")
            return {"error": "Interview engine not initialized. Please initialize first."}
        
        try:
            # Start the interview
            result = self.interview_engine.start_interview()
            logger.info("Interview started successfully")
            
            # Return the introduction and first question
            return result
            
        except Exception as e:
            logger.error(f"Error starting interview: {str(e)}")
            return {"error": f"Failed to start interview: {str(e)}"}
    
    def process_response(self, response_text: str) -> Dict[str, Any]:
        """Process a candidate's response and get the next question or follow-up."""
        if not self.interview_engine or not self.interview_engine.interview_active:
            logger.error("No active interview session")
            return {"error": "No active interview session. Please start an interview first."}
        
        try:
            # Log the beginning of the response (truncated for privacy)
            truncated_log = response_text[:30] + '...' if len(response_text) > 30 else response_text
            logger.info(f"Processing response: '{truncated_log}'")
            
            # Process the response with error handling
            try:
                result = self.interview_engine.process_response(response_text)
                if not result or not isinstance(result, dict):
                    logger.error(f"Invalid response format from engine: {result}")
                    return {"error": "Invalid response format", "status": "error", "message": "An error occurred processing your response. Please try again."}
                
                # Make a copy to avoid modifying the original
                response_data = dict(result)
                
                # Ensure all required fields are present
                if 'status' not in response_data:
                    response_data['status'] = 'active'
                
                # If interview is complete, save the interview data
                if result.get("status") == "complete":
                    self._save_interview_data()
                
                return response_data
                
            except Exception as e:
                # Catch any engine processing errors
                logger.error(f"Error in engine.process_response: {str(e)}")
                
                # Try to recover by moving to the next question
                try:
                    next_question = self.interview_engine.get_next_question()
                    if next_question:
                        return {
                            "status": "active",
                            "acknowledgment": "Thank you for your response. Let's continue with the next question.",
                            "question": next_question,
                            "question_number": self.interview_engine.current_question_index + 1,
                            "total_questions": len(self.interview_engine.questions)
                        }
                    else:
                        self.interview_engine.interview_complete = True
                        return {
                            "status": "complete",
                            "closing_remarks": "Thank you for your time today. This concludes our interview.",
                            "summary": {"overall_impression": "The interview has been completed."}
                        }
                except Exception as recovery_error:
                    logger.error(f"Failed to recover from processing error: {str(recovery_error)}")
                    return {"error": "Failed to process response", "status": "error", "message": "An error occurred. Please refresh the page and try again."}
        
        except Exception as outer_error:
            # Catch any JSON parsing or other errors
            logger.error(f"Outer error in process_response route: {str(outer_error)}")
            return {"error": "Server error", "status": "error", "message": "A server error occurred. Please refresh the page and try again."}
    
    def _save_interview_data(self) -> None:
        """Save the complete interview data."""
        if not self.interview_engine:
            return
        
        try:
            # Get the full interview data
            interview_data = self.interview_engine.get_interview_data()
            
            # Generate a filename based on candidate name and job title
            candidate_name = interview_data.get("candidate_data", {}).get("name", "candidate")
            job_title = interview_data.get("job_data", {}).get("title", "position")
            sanitized_name = candidate_name.lower().replace(" ", "_")
            sanitized_title = job_title.lower().replace(" ", "_")
            
            timestamp = int(time.time())
            filename = f"{sanitized_name}_{sanitized_title}_{timestamp}.json"
            
            # Save to the interviews directory
            with open(DATA_DIR / "interviews" / filename, "w") as f:
                json.dump(interview_data, f, indent=2)
            
            logger.info(f"Interview data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving interview data: {str(e)}")
    
    def get_interview_summary(self) -> Dict[str, Any]:
        """Get the summary of a completed interview."""
        if not self.interview_engine:
            logger.error("Interview engine not initialized")
            return {"error": "Interview engine not initialized."}
        
        if not self.interview_engine.interview_complete:
            logger.error("Interview not complete")
            return {"error": "Interview is not complete yet. Cannot generate summary."}
        
        try:
            return self.interview_engine.summary
        except Exception as e:
            logger.error(f"Error getting interview summary: {str(e)}")
            return {"error": f"Failed to get interview summary: {str(e)}"}
    
    def load_sample_data(self):
        """Load sample data for testing purposes."""
        logger.info("Loading sample data for testing")
        
        # Sample job data
        self.job_data = {
            "title": "Software Engineer",
            "description": "We are looking for a skilled Software Engineer to join our development team. You will be responsible for designing, implementing, and maintaining high-quality software solutions.",
            "requirements": [
                "Strong proficiency in Python, JavaScript, and web development frameworks",
                "Experience with API design and implementation",
                "Knowledge of database systems and data modeling",
                "Familiarity with cloud platforms (AWS, Azure, or GCP)",
                "Excellent problem-solving and communication skills"
            ]
        }
        
        # Sample company data
        self.company_data = {
            "name": "TechInnovate Solutions",
            "description": "A leading provider of innovative software solutions.",
            "mission": "To create technology that empowers businesses and improves lives.",
            "vision": "To be the global leader in innovative software solutions.",
            "values": [
                "Innovation",
                "Collaboration",
                "Excellence",
                "Integrity",
                "Customer Focus"
            ]
        }
        
        # Sample candidate data
        self.candidate_data = {
            "name": "Alex Johnson",
            "skills": [
                "Python",
                "JavaScript",
                "React",
                "Node.js",
                "SQL",
                "Git",
                "AWS"
            ],
            "experience": "5 years of software development experience",
            "background": "Computer Science degree from University of Technology, previously worked at StartupX and BigTechCorp."
        }
        
        # Save the sample data
        self._save_processed_data()
        
        logger.info("Sample data loaded successfully")
        return True
    
    def run_interactive_interview(self):
        """Run the interview in interactive mode via the command line."""
        logger.info("Starting interactive interview mode")
        
        print("\n===== AI Interview Agent =====\n")
        
        # Initialize the interview
        init_result = self.initialize_interview()
        if "error" in init_result:
            print(f"Error: {init_result['error']}")
            return
        
        # Start the interview
        start_result = self.start_interview()
        if "error" in start_result:
            print(f"Error: {start_result['error']}")
            return
        
        # Display introduction
        print(f"\nInterviewer: {start_result['introduction']}\n")
        
        # Main interview loop
        current_result = start_result
        while current_result.get("status") == "active":
            # Display the current question
            question = current_result["question"]["question"]
            print(f"Interviewer: {question}")
            
            # Get candidate's response
            print("\nYou: ", end="")
            response = input()
            
            # Process the response
            current_result = self.process_response(response)
            
            if "error" in current_result:
                print(f"Error: {current_result['error']}")
                break
            
            print()  # Add a blank line for readability
        
        # Display closing and summary
        if current_result.get("status") == "complete":
            print(f"Interviewer: {current_result['closing_remarks']}\n")
            
            print("\n===== Interview Summary =====\n")
            summary = current_result["summary"]
            
            if "candidate_name" in summary and "position" in summary:
                print(f"Candidate: {summary['candidate_name']}")
                print(f"Position: {summary['position']}\n")
            
            if "strengths" in summary:
                print("Strengths:")
                for strength in summary["strengths"]:
                    print(f"- {strength}")
                print()
            
            if "areas_for_improvement" in summary:
                print("Areas for Improvement:")
                for area in summary["areas_for_improvement"]:
                    print(f"- {area}")
                print()
            
            if "technical_evaluation" in summary:
                print(f"Technical Evaluation: {summary['technical_evaluation']}\n")
            
            if "cultural_fit" in summary:
                print(f"Cultural Fit: {summary['cultural_fit']}\n")
            
            if "recommendation" in summary:
                print(f"Recommendation: {summary['recommendation']}\n")
            
            if "next_steps" in summary:
                print(f"Next Steps: {summary['next_steps']}\n")
            
            if "overall_assessment" in summary:
                print(f"Overall Assessment: {summary['overall_assessment']}\n")
            
            print("\nInterview data has been saved to the 'data/interviews' directory.")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="AI Interview Agent")
    parser.add_argument("--job", help="Path to job description file")
    parser.add_argument("--company", help="Path to company profile file")
    parser.add_argument("--resume", help="Path to candidate resume file")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive interview mode")
    parser.add_argument("--demo", action="store_true", help="Run with sample data for demonstration")
    
    args = parser.parse_args()
    
    # Create the application
    app = InterviewApp()
    
    # Process documents if specified
    if any([args.job, args.company, args.resume]):
        success = app.process_documents(args.job, args.company, args.resume)
        if success:
            print("Documents processed successfully.")
        else:
            print("Error processing documents. See logs for details.")
            return
    
    # Load sample data if demo mode
    if args.demo:
        app.load_sample_data()
        print("Loaded sample data for demonstration.")
        app.run_interactive_interview()
        return
    
    # Run in interactive mode if requested
    if args.interactive:
        app.run_interactive_interview()
        return
    
    # If no interactive mode and no documents, show help
    if not any([args.job, args.company, args.resume, args.interactive, args.demo]):
        print("No action specified. Use --interactive for interactive mode, --demo for demonstration, or specify documents to process.")
        parser.print_help()


if __name__ == "__main__":
    main() 