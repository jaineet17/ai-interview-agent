import unittest
from unittest.mock import MagicMock, patch
import json

from interview_engine import InterviewEngine
from interview_engine.interview_generator import InterviewGenerator

class TestInterviewEngine(unittest.TestCase):
    """Test cases for the InterviewEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_generator = MagicMock(spec=InterviewGenerator)
        
        # Mock data
        self.job_data = {
            "title": "Software Engineer",
            "description": "Building innovative software solutions",
            "required_skills": ["Python", "JavaScript", "API design"]
        }
        
        self.company_data = {
            "name": "Tech Innovations Inc.",
            "description": "Leading technology company",
            "values": "Innovation, Collaboration, Excellence"
        }
        
        self.candidate_data = {
            "name": "Alex Johnson",
            "experience": "5 years of software development",
            "background": "Computer Science degree"
        }
        
        # Mock interview script
        self.mock_script = {
            "introduction": "Welcome to the interview!",
            "questions": {
                "job_specific": [
                    {
                        "question": "Tell me about your experience with Python",
                        "purpose": "To assess Python skills",
                        "good_answer_criteria": "Specific examples and projects"
                    }
                ],
                "technical": [
                    {
                        "question": "Explain RESTful API design",
                        "purpose": "To assess API knowledge",
                        "good_answer_criteria": "Understanding of REST principles"
                    }
                ],
                "company_fit": [
                    {
                        "question": "How do you approach collaboration?",
                        "purpose": "To assess team fit",
                        "good_answer_criteria": "Examples of successful collaboration"
                    }
                ],
                "behavioral": [
                    {
                        "question": "Describe a challenging project",
                        "purpose": "To assess problem-solving",
                        "good_answer_criteria": "Clear problem definition and resolution"
                    }
                ]
            },
            "closing": "Thank you for your time today."
        }
        
        # Set up mock return values
        self.mock_generator.generate_interview_script.return_value = self.mock_script
        self.mock_generator.generate_follow_up.return_value = "Can you elaborate on that?"
        
        # Create the interview engine with mocked dependencies
        self.engine = InterviewEngine(
            job_data=self.job_data,
            company_data=self.company_data,
            candidate_data=self.candidate_data,
            interview_generator=self.mock_generator
        )
    
    def test_init(self):
        """Test initialization of InterviewEngine."""
        self.assertEqual(self.engine.job_data, self.job_data)
        self.assertEqual(self.engine.company_data, self.company_data)
        self.assertEqual(self.engine.candidate_data, self.candidate_data)
        self.assertEqual(self.engine.generator, self.mock_generator)
        self.assertFalse(self.engine.interview_active)
        self.assertFalse(self.engine.interview_complete)
    
    def test_generate_interview_script(self):
        """Test generation of interview script."""
        script = self.engine.generate_interview_script()
        
        # Verify the mock was called
        self.mock_generator.generate_interview_script.assert_called_once_with(
            self.job_data, self.company_data, self.candidate_data
        )
        
        # Verify script was set and returned
        self.assertEqual(script, self.mock_script)
        self.assertEqual(self.engine.script, self.mock_script)
        
        # Verify questions were organized
        self.assertTrue(len(self.engine.questions) > 0)
    
    def test_organize_questions(self):
        """Test question organization."""
        # Generate script to set up questions
        self.engine.generate_interview_script()
        
        # Verify questions were organized properly
        questions = self.engine.questions
        
        # Should include intro + questions from all categories + closing
        expected_min_length = 1 + 1 + 1 + 1 + 1 + 1
        self.assertGreaterEqual(len(questions), expected_min_length)
        
        # Verify first question is introduction
        self.assertEqual(questions[0]["category"], "introduction")
        
        # Verify last question is closing
        self.assertEqual(questions[-1]["category"], "closing")
    
    def test_start_interview(self):
        """Test starting an interview."""
        # Start the interview
        result = self.engine.start_interview()
        
        # Verify interview state
        self.assertTrue(self.engine.interview_active)
        self.assertEqual(self.engine.current_question_index, 0)
        self.assertEqual(len(self.engine.responses), 0)
        
        # Verify result structure
        self.assertEqual(result["status"], "active")
        self.assertEqual(result["introduction"], self.mock_script["introduction"])
        self.assertEqual(result["question"], self.engine.questions[0])
        self.assertEqual(result["question_number"], 1)
    
    def test_get_current_question(self):
        """Test getting the current question."""
        # Generate script and start interview to set up questions
        self.engine.generate_interview_script()
        self.engine.start_interview()
        
        # Get current question
        question = self.engine.get_current_question()
        
        # Verify it's the first question
        self.assertEqual(question, self.engine.questions[0])
    
    def test_get_next_question(self):
        """Test getting the next question."""
        # Generate script and start interview to set up questions
        self.engine.generate_interview_script()
        self.engine.start_interview()
        
        # Get next question
        next_question = self.engine.get_next_question()
        
        # Verify it moved to the next question
        self.assertEqual(self.engine.current_question_index, 1)
        self.assertEqual(next_question, self.engine.questions[1])
    
    def test_process_response_with_follow_up(self):
        """Test processing a response that generates a follow-up."""
        # Generate script and start interview
        self.engine.generate_interview_script()
        self.engine.start_interview()
        
        # Process a response that will generate a follow-up
        result = self.engine.process_response("This is my response")
        
        # Verify response was stored
        self.assertEqual(len(self.engine.responses), 1)
        self.assertEqual(self.engine.responses[0]["response"], "This is my response")
        
        # Verify follow-up was generated
        self.assertEqual(len(self.engine.follow_ups), 1)
        
        # Verify result contains follow-up
        self.assertEqual(result["status"], "active")
        self.assertTrue(result["is_follow_up"])
        self.assertEqual(result["question"]["question"], "Can you elaborate on that?")
        
        # Verify we stayed on the same question
        self.assertEqual(self.engine.current_question_index, 0)
    
    def test_process_response_move_to_next(self):
        """Test processing a response and moving to the next question."""
        # Generate script and start interview
        self.engine.generate_interview_script()
        self.engine.start_interview()
        
        # Set up mock to not return a follow-up this time
        self.mock_generator.generate_follow_up.return_value = None
        
        # Process a response
        result = self.engine.process_response("This is my response")
        
        # Verify response was stored
        self.assertEqual(len(self.engine.responses), 1)
        
        # Verify no follow-up was generated
        self.assertEqual(len(self.engine.follow_ups), 0)
        
        # Verify result moves to next question
        self.assertEqual(result["status"], "active")
        self.assertFalse(result["is_follow_up"])
        self.assertEqual(result["question"], self.engine.questions[1])
        
        # Verify we moved to the next question
        self.assertEqual(self.engine.current_question_index, 1)
    
    def test_process_response_complete_interview(self):
        """Test processing the final response to complete the interview."""
        # Generate script and start interview
        self.engine.generate_interview_script()
        self.engine.start_interview()
        
        # Set up mock to not return a follow-up
        self.mock_generator.generate_follow_up.return_value = None
        
        # Set up mock for summary generation
        mock_summary = {"recommendation": "Recommend hiring"}
        self.mock_generator.generate_interview_summary.return_value = mock_summary
        
        # Force the current question to be the last one
        self.engine.current_question_index = len(self.engine.questions) - 1
        
        # Process the final response
        result = self.engine.process_response("This is my final response")
        
        # Verify interview is complete
        self.assertTrue(self.engine.interview_complete)
        self.assertFalse(self.engine.interview_active)
        
        # Verify summary was generated
        self.assertEqual(self.engine.summary, mock_summary)
        
        # Verify result indicates completion
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["closing_remarks"], self.mock_script["closing"])
        self.assertEqual(result["summary"], mock_summary)
    
    def test_generate_summary(self):
        """Test generating an interview summary."""
        # Generate script
        self.engine.generate_interview_script()
        
        # Set up some mock responses
        self.engine.responses = [
            {"question_index": 0, "question": "Q1", "category": "introduction", "response": "R1"},
            {"question_index": 1, "question": "Q2", "category": "job_specific", "response": "R2"}
        ]
        
        # Mark interview as complete
        self.engine.interview_complete = True
        
        # Set up mock summary
        mock_summary = {"recommendation": "Recommend hiring"}
        self.mock_generator.generate_interview_summary.return_value = mock_summary
        
        # Generate summary
        summary = self.engine.generate_summary()
        
        # Verify summary generation
        self.mock_generator.generate_interview_summary.assert_called_once()
        self.assertEqual(summary, mock_summary)
    
    def test_get_interview_state(self):
        """Test getting the interview state."""
        # Generate script and start interview
        self.engine.generate_interview_script()
        self.engine.start_interview()
        
        # Add a mock response
        self.engine.responses.append({"response": "Test response"})
        
        # Get state
        state = self.engine.get_interview_state()
        
        # Verify state
        self.assertTrue(state["active"])
        self.assertFalse(state["complete"])
        self.assertEqual(state["current_question_index"], 0)
        self.assertEqual(state["total_questions"], len(self.engine.questions))
        self.assertEqual(state["responses_count"], 1)
    
    def test_get_interview_data(self):
        """Test getting all interview data."""
        # Generate script and start interview
        self.engine.generate_interview_script()
        self.engine.start_interview()
        
        # Get data
        data = self.engine.get_interview_data()
        
        # Verify data structure
        self.assertEqual(data["job_data"], self.job_data)
        self.assertEqual(data["company_data"], self.company_data)
        self.assertEqual(data["candidate_data"], self.candidate_data)
        self.assertEqual(data["script"], self.mock_script)
        self.assertEqual(data["questions"], self.engine.questions)
        self.assertEqual(data["responses"], self.engine.responses)
        self.assertEqual(data["state"], self.engine.get_interview_state())


if __name__ == "__main__":
    unittest.main() 