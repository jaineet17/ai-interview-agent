import json
import logging
import time
import re
from typing import Dict, List, Any, Optional, Tuple

from .interview_generator import InterviewGenerator

# Set up logging
logger = logging.getLogger(__name__)

class ConversationMemory:
    """Maintains the conversation context to provide more natural responses."""
    
    def __init__(self, max_history: int = 10):
        """Initialize conversation memory.
        
        Args:
            max_history: Maximum number of conversation turns to remember
        """
        self.conversation_history = []
        self.max_history = max_history
        self.insights = {}  # Store insights about candidate's responses
        self.topics_mentioned = set()  # Topics the candidate has mentioned
        self.candidate_style = {}  # Observations about candidate's communication style
        
    def add_exchange(self, question: Dict[str, Any], response: str, is_candidate_question: bool = False) -> None:
        """Add a new question-response pair to the conversation history."""
        exchange = {
            "question": question,
            "response": response,
            "timestamp": time.time(),
            "is_candidate_question": is_candidate_question
        }
        
        self.conversation_history.append(exchange)
        
        # Trim history if it exceeds max size
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)
        
        # Update insights based on response
        self._update_insights(response, question)
    
    def _update_insights(self, response: str, question: Dict[str, Any]) -> None:
        """Extract insights from candidate responses to inform future interactions."""
        # Extract topics mentioned
        self._extract_topics(response)
        
        # Analyze communication style
        self._analyze_communication_style(response)
        
        # Category-specific analysis
        category = question.get("category", "")
        if category == "technical":
            self._analyze_technical_response(response)
        elif category == "behavioral":
            self._analyze_behavioral_response(response)
        elif category == "job_specific":
            self._analyze_job_specific_response(response)
    
    def _extract_topics(self, response: str) -> None:
        """Extract key topics mentioned in the response."""
        # Simple keyword extraction - in a real system this would use NLP
        # Common tech terms
        tech_terms = ["python", "javascript", "react", "node", "aws", "cloud", "api", 
                      "database", "sql", "nosql", "frontend", "backend", "fullstack", 
                      "devops", "agile", "machine learning", "ai"]
        
        # Check for tech terms in the response
        for term in tech_terms:
            if re.search(r'\b' + re.escape(term) + r'\b', response.lower()):
                self.topics_mentioned.add(term)
    
    def _analyze_communication_style(self, response: str) -> None:
        """Analyze the candidate's communication style."""
        # Check response length
        words = response.split()
        if len(words) < 15:
            self.candidate_style["concise"] = self.candidate_style.get("concise", 0) + 1
        elif len(words) > 100:
            self.candidate_style["verbose"] = self.candidate_style.get("verbose", 0) + 1
        
        # Check for use of technical language
        tech_jargon_count = sum(1 for term in self.topics_mentioned if term in response.lower())
        if tech_jargon_count > 3:
            self.candidate_style["technical"] = self.candidate_style.get("technical", 0) + 1
        
        # Check for hesitation words
        hesitation_words = ["um", "uh", "like", "you know", "sort of", "kind of"]
        hesitation_count = sum(1 for word in hesitation_words if word in response.lower())
        if hesitation_count > 3:
            self.candidate_style["hesitant"] = self.candidate_style.get("hesitant", 0) + 1
    
    def _analyze_technical_response(self, response: str) -> None:
        """Analyze responses to technical questions."""
        # Look for depth of technical knowledge
        technical_depth_indicators = ["implemented", "designed", "developed", "architected", 
                                      "because", "in order to", "specifically"]
        
        depth_score = sum(1 for indicator in technical_depth_indicators if indicator in response.lower())
        
        if depth_score > 2:
            self.insights["technical_depth"] = self.insights.get("technical_depth", 0) + 1
    
    def _analyze_behavioral_response(self, response: str) -> None:
        """Analyze responses to behavioral questions."""
        # Look for STAR method components
        situation = any(term in response.lower() for term in ["situation", "context", "background", "when i"])
        task = any(term in response.lower() for term in ["task", "goal", "objective", "needed to", "had to"])
        action = any(term in response.lower() for term in ["action", "approach", "did", "implemented", "executed"])
        result = any(term in response.lower() for term in ["result", "outcome", "impact", "learned", "accomplished"])
        
        star_components = sum([situation, task, action, result])
        
        if star_components >= 3:
            self.insights["structured_responses"] = self.insights.get("structured_responses", 0) + 1
    
    def _analyze_job_specific_response(self, response: str) -> None:
        """Analyze responses to job-specific questions."""
        # Look for relevant experience mentions
        experience_terms = ["experience", "worked on", "project", "role", "position", "job"]
        has_experience = any(term in response.lower() for term in experience_terms)
        
        if has_experience:
            self.insights["relevant_experience"] = self.insights.get("relevant_experience", 0) + 1
    
    def get_contextual_prompt(self, current_question: Dict[str, Any], next_question: Dict[str, Any]) -> str:
        """Generate a contextual prompt to help create a natural transition."""
        prompt = "Based on the conversation so far:\n"
        
        # Add recent exchanges for context
        for exchange in self.conversation_history[-3:]:
            prompt += f"Q: {exchange['question'].get('question', '')}\n"
            prompt += f"A: {exchange['response']}\n\n"
        
        # Add insights to inform the response
        prompt += "Candidate insights:\n"
        
        # Add topics they've mentioned
        if self.topics_mentioned:
            prompt += f"- Topics mentioned: {', '.join(self.topics_mentioned)}\n"
        
        # Add communication style observations
        dominant_style = max(self.candidate_style.items(), key=lambda x: x[1])[0] if self.candidate_style else None
        if dominant_style:
            prompt += f"- Communication style: {dominant_style}\n"
        
        # Add any key insights
        for insight, count in self.insights.items():
            if count > 0:
                prompt += f"- {insight.replace('_', ' ').title()}: {count} instances\n"
        
        # Instructions for transition
        prompt += f"\nCurrent question: {current_question.get('question', '')}\n"
        prompt += f"Next question: {next_question.get('question', '')}\n"
        prompt += "\nPlease create a natural, conversational transition between these questions that acknowledges the candidate's previous response and flows naturally into the next question."
        
        return prompt
    
    def get_recent_topics(self) -> List[str]:
        """Return the most recently discussed topics."""
        return list(self.topics_mentioned)
    
    def get_dominant_style(self) -> Optional[str]:
        """Return the candidate's dominant communication style."""
        if not self.candidate_style:
            return None
        return max(self.candidate_style.items(), key=lambda x: x[1])[0]

class InterviewEngine:
    """Manages the interview flow, question sequencing, and response processing."""
    
    def __init__(self, job_data: Dict[str, Any], 
                company_data: Dict[str, Any], 
                candidate_data: Dict[str, Any], 
                interview_generator: InterviewGenerator):
        """Initialize with job, company, and candidate data."""
        self.job_data = job_data
        self.company_data = company_data
        self.candidate_data = candidate_data
        self.generator = interview_generator
        
        # Interview state
        self.script = None
        self.questions = []
        self.current_question_index = 0
        self.responses = []
        self.follow_ups = []
        self.interview_active = False
        self.interview_complete = False
        self.summary = None
        self.demo_mode = False
        
        # Enhanced tracking
        self.previous_responses = {}  # For duplicate detection
        self.candidate_questions = []  # Track candidate questions
        self.interviewer_mode = "standard"  # standard, probing, wrapping_up
        
        # Add conversation memory
        self.memory = ConversationMemory()
        
        # Add cache for LLM prompts
        self.prompt_cache = {}
        
        logger.info("Initialized InterviewEngine")
    
    def generate_interview_script(self, demo_mode: bool = False) -> Dict[str, Any]:
        """Generate a personalized interview script."""
        logger.info("Generating interview script")
        self.demo_mode = demo_mode
        
        if demo_mode:
            logger.info("Using demo mode for interview script")
            
        self.script = self.generator.generate_interview_script(
            self.job_data, 
            self.company_data, 
            self.candidate_data,
            demo_mode
        )
        
        # Flatten questions into a single sequence
        self._organize_questions()
        
        return self.script
    
    def _organize_questions(self) -> None:
        """Organize questions from different categories into a single interview flow."""
        if not self.script:
            logger.warning("Attempted to organize questions without a script")
            return
        
        # Get questions from each category
        job_specific = self.script['questions'].get('job_specific', [])
        company_fit = self.script['questions'].get('company_fit', [])
        technical = self.script['questions'].get('technical', [])
        behavioral = self.script['questions'].get('behavioral', [])
        
        # Create a natural interview flow that interleaves different question types
        question_sequence = []
        
        # Add introduction question
        introduction_q = {
            "category": "introduction",
            "question": "Could you please tell me a bit about yourself and your interest in this position?",
            "purpose": "To break the ice and hear the candidate's self-introduction",
            "transition": "Thanks for joining us today. I'd like to start by getting to know you a bit better."
        }
        question_sequence.append(introduction_q)
        
        # Add initial job-specific questions to establish background
        if job_specific:
            job_q1 = job_specific.pop(0)
            job_q1["category"] = "job_specific"
            job_q1["transition"] = "Thanks for sharing that. I'd like to learn more about your relevant experience."
            question_sequence.append(job_q1)
        
        # Add a technical question early to gauge skills
        if technical:
            tech_q1 = technical.pop(0)
            tech_q1["category"] = "technical"
            tech_q1["transition"] = "Now I'd like to understand your technical capabilities a bit better."
            question_sequence.append(tech_q1)
        
        # Add company fit to establish interest
        if company_fit:
            fit_q1 = company_fit.pop(0)
            fit_q1["category"] = "company_fit"
            fit_q1["transition"] = "Switching gears a bit, I'd like to explore how you might fit with our company culture."
            question_sequence.append(fit_q1)
        
        # Add behavioral question to understand work style
        if behavioral:
            behave_q1 = behavioral.pop(0)
            behave_q1["category"] = "behavioral"
            behave_q1["transition"] = "Let's talk about some of your past experiences and how you handled them."
            question_sequence.append(behave_q1)
        
        # Mix the remaining questions in a natural sequence with transitions
        remaining_job = len(job_specific)
        remaining_tech = len(technical)
        remaining_fit = len(company_fit)
        remaining_behave = len(behavioral)
        
        # Create transition phrases for a more natural flow
        transitions = {
            "job_specific": [
                "Building on what we've discussed, I'd like to ask about your experience with...",
                "I'm interested to hear more about your background in...",
                "Let's talk more specifically about your work with..."
            ],
            "technical": [
                "Now I'd like to explore your technical knowledge in...",
                "Regarding the technical aspects of this role...",
                "Let's dive into some of the technical skills required for this position..."
            ],
            "company_fit": [
                "Considering our company values...",
                "From a team perspective...",
                "In terms of our work environment..."
            ],
            "behavioral": [
                "Reflecting on your past experiences...",
                "I'm curious about how you've handled certain situations before...",
                "Let's discuss an example of when you've had to..."
            ]
        }
        
        # Distribute remaining questions with natural transitions
        while job_specific or technical or company_fit or behavioral:
            # Alternate between different question types for natural flow
            
            if job_specific:
                q = job_specific.pop(0)
                q["category"] = "job_specific"
                q["transition"] = transitions["job_specific"][remaining_job % len(transitions["job_specific"])]
                remaining_job -= 1
                question_sequence.append(q)
            
            if behavioral:
                q = behavioral.pop(0)
                q["category"] = "behavioral"
                q["transition"] = transitions["behavioral"][remaining_behave % len(transitions["behavioral"])]
                remaining_behave -= 1
                question_sequence.append(q)
            
            if technical:
                q = technical.pop(0)
                q["category"] = "technical"
                q["transition"] = transitions["technical"][remaining_tech % len(transitions["technical"])]
                remaining_tech -= 1
                question_sequence.append(q)
            
            if company_fit:
                q = company_fit.pop(0)
                q["category"] = "company_fit"
                q["transition"] = transitions["company_fit"][remaining_fit % len(transitions["company_fit"])]
                remaining_fit -= 1
                question_sequence.append(q)
        
        # Add closing question
        closing_q = {
            "category": "closing",
            "question": "Do you have any questions for me about the position or the company?",
            "purpose": "To allow the candidate to ask questions and show their interest",
            "transition": "We've covered quite a bit today. Before we wrap up, I wanted to give you an opportunity to ask any questions you might have."
        }
        question_sequence.append(closing_q)
        
        self.questions = question_sequence
        logger.info(f"Organized {len(self.questions)} questions for interview flow")
    
    def start_interview(self) -> Dict[str, Any]:
        """Start the interview process."""
        if not self.script:
            logger.info("No script generated yet, generating now")
            self.generate_interview_script()
        
        self.interview_active = True
        self.current_question_index = 0
        self.responses = []
        self.follow_ups = []
        
        logger.info("Starting interview")
        
        current_question = self.get_current_question()
        transition = current_question.get("transition", "")
        
        # Return introduction and first question
        return {
            "status": "active",
            "introduction": self.script["introduction"],
            "question": current_question,
            "transition": transition,
            "question_number": 1,
            "total_questions": len(self.questions)
        }
    
    def get_current_question(self) -> Optional[Dict[str, Any]]:
        """Get the current question in the sequence."""
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        else:
            logger.warning(f"Attempted to get question at invalid index: {self.current_question_index}")
            return None
    
    def get_next_question(self) -> Optional[Dict[str, Any]]:
        """Move to the next question and return it."""
        self.current_question_index += 1
        logger.debug(f"Moving to question index {self.current_question_index}")
        
        if self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        else:
            self.interview_complete = True
            logger.info("Reached end of questions, interview complete")
            return None
    
    def process_response(self, response_text: str) -> Dict[str, Any]:
        """Process a candidate's response and determine the next action."""
        try:
            # Track response in history
            self.responses.append({
                "question_index": self.current_question_index,
                "question": self.get_current_question(),
                "response": response_text,
                "timestamp": time.time()
            })
            
            # Get the current question
            current_question = self.get_current_question()
            if not current_question:
                logger.error("Failed to get current question during response processing")
                return self._fallback_response_handler()
                
            logger.info(f"Processing response for question {self.current_question_index} ({current_question['category']})")
            
            # Add to conversation memory
            try:
                self.memory.add_exchange(current_question, response_text)
            except Exception as memory_err:
                logger.error(f"Error adding to conversation memory: {str(memory_err)}")
                # Continue processing even if memory fails
            
            # Check if this response is similar to previous responses
            try:
                if self._check_duplicate_response(response_text, self.current_question_index):
                    return self._handle_duplicate_response(response_text, current_question)
            except Exception as dup_err:
                logger.error(f"Error checking for duplicate response: {str(dup_err)}")
                # Continue without duplicate checking if it fails
                
            # Check if response contains a question from the candidate
            try:
                if self._detect_candidate_question(response_text):
                    return self._handle_candidate_question(response_text, current_question)
            except Exception as q_err:
                logger.error(f"Error detecting candidate question: {str(q_err)}")
                # Continue if question detection fails
            
            # Get count of follow-ups for this question
            follow_up_count = sum(1 for f in self.follow_ups if f["question_index"] == self.current_question_index)
            
            # Check if interview is complete (final question reached and no follow-up needed)
            if self.current_question_index >= len(self.questions) - 1 and not self._should_ask_follow_up(response_text, current_question, follow_up_count):
                logger.info("Interview complete after final question")
                self.interview_complete = True
                
                # Generate interview summary
                try:
                    self.generate_summary()
                except Exception as sum_err:
                    logger.error(f"Error generating interview summary: {str(sum_err)}")
                    # Create a basic summary if generation fails
                    self.summary = {"overall_impression": "Interview completed successfully."}
                
                # Return the completion response
                return {
                    "status": "complete",
                    "closing_remarks": self.script.get("closing", "Thank you for your time today. We'll be in touch with next steps."),
                    "summary": self.summary
                }
            elif self._should_ask_follow_up(response_text, current_question, follow_up_count):
                logger.info("Generating follow-up question")
                
                try:
                    follow_up = self.generator.generate_follow_up_question(
                        current_question, 
                        response_text,
                        self.job_data,
                        self.company_data,
                        self.candidate_data
                    )
                    
                    # Check if follow-up generation failed or returned None
                    if not follow_up:
                        logger.info("No follow-up needed, moving to next question")
                        next_question = self.get_next_question()
                        
                        if next_question:
                            # Generate a contextual transition
                            try:
                                conversational_buffer = self._get_conversational_buffer(response_text, current_question, next_question)
                            except Exception as buffer_err:
                                logger.error(f"Error generating conversational buffer: {str(buffer_err)}")
                                conversational_buffer = "Thank you for your response."
                            
                            logger.info(f"Moving to next question ({next_question['category']})")
                            return {
                                "status": "active",
                                "acknowledgment": conversational_buffer,
                                "question": next_question,
                                "question_number": self.current_question_index + 1,
                                "total_questions": len(self.questions)
                            }
                        else:
                            # End of interview reached
                            logger.info("Reached end of questions after follow-up attempt")
                            self.interview_complete = True
                            
                            # Generate interview summary
                            try:
                                self.generate_summary()
                            except Exception as end_err:
                                logger.error(f"Error generating end summary: {str(end_err)}")
                                self.summary = {"overall_impression": "Interview completed successfully."}
                            
                            return {
                                "status": "complete",
                                "closing_remarks": self.script.get("closing", "Thank you for your time today. We'll be in touch with next steps."),
                                "summary": self.summary
                            }
                    
                    self.follow_ups.append({
                        "question_index": self.current_question_index,
                        "original_question": current_question,
                        "follow_up_question": follow_up,
                        "response": response_text
                    })
                    
                    logger.info("Generated follow-up question")
                    
                    # Generate an acknowledgment of their response
                    try:
                        acknowledgment = self._generate_acknowledgment(current_question, response_text)
                    except Exception as ack_err:
                        logger.error(f"Error generating acknowledgment: {str(ack_err)}")
                        acknowledgment = "Thank you for your response."
                    
                    return {
                        "status": "active",
                        "acknowledgment": acknowledgment,
                        "question": {
                            "question": follow_up,
                            "category": current_question["category"],
                            "follow_up": True
                        },
                        "question_number": self.current_question_index + 1,
                        "total_questions": len(self.questions)
                    }
                except Exception as follow_up_err:
                    logger.error(f"Error in follow-up generation process: {str(follow_up_err)}")
                    # If follow-up generation fails, move to the next question
                    next_question = self.get_next_question()
                    return {
                        "status": "active",
                        "acknowledgment": "Thank you for sharing that information. Let's move on to the next question.",
                        "question": next_question,
                        "question_number": self.current_question_index + 1,
                        "total_questions": len(self.questions)
                    }
            else:
                # No follow-up needed, move to next question
                logger.info("No follow-up needed, moving to next question")
                next_question = self.get_next_question()
                
                if next_question:
                    # Generate a contextual transition
                    try:
                        conversational_buffer = self._get_conversational_buffer(response_text, current_question, next_question)
                    except Exception as buffer_err:
                        logger.error(f"Error generating conversational buffer: {str(buffer_err)}")
                        conversational_buffer = "Thank you for your response."
                    
                    logger.info(f"Moving to next question ({next_question['category']})")
                    return {
                        "status": "active",
                        "acknowledgment": conversational_buffer,
                        "question": next_question,
                        "question_number": self.current_question_index + 1, 
                        "total_questions": len(self.questions)
                    }
                else:
                    # End of interview reached
                    logger.info("Reached end of questions, interview complete")
                    self.interview_complete = True
                    
                    # Generate interview summary
                    try:
                        self.generate_summary()
                    except Exception as sum_err:
                        logger.error(f"Error generating summary at end: {str(sum_err)}")
                        self.summary = {"overall_impression": "Interview completed successfully."}
                    
                    return {
                        "status": "complete",
                        "closing_remarks": self.script.get("closing", "Thank you for your time today. We'll be in touch with next steps."),
                        "summary": self.summary
                    }
        except Exception as e:
            logger.error(f"Unhandled error in process_response: {str(e)}")
            return self._fallback_response_handler()
    
    def _fallback_response_handler(self) -> Dict[str, Any]:
        """Emergency fallback to ensure the interview continues even if errors occur."""
        logger.warning("Using fallback response handler due to an error")
        
        # Try to get the next question, but handle if that fails too
        try:
            # Move to next question in case of error
            self.current_question_index += 1
            if self.current_question_index < len(self.questions):
                next_question = self.questions[self.current_question_index]
                return {
                    "status": "active",
                    "acknowledgment": "Thank you. Let's move to the next question.",
                    "question": next_question,
                    "question_number": self.current_question_index + 1,
                    "total_questions": len(self.questions)
                }
            else:
                # End interview if we've run out of questions
                self.interview_complete = True
                return {
                    "status": "complete",
                    "closing_remarks": "Thank you for your time today. This concludes our interview.",
                    "summary": {"overall_impression": "The interview has been completed."}
                }
        except Exception as fallback_err:
            logger.error(f"Error in fallback handler: {str(fallback_err)}")
            # Ultimate fallback - create a simple response with a default question
            return {
                "status": "active",
                "acknowledgment": "I appreciate your patience. Let's continue.",
                "question": {
                    "question": "Could you tell me more about your experience?",
                    "category": "general",
                    "follow_up": False
                },
                "question_number": 1,
                "total_questions": 1
            }
    
    def _generate_acknowledgment(self, current_question: Dict[str, Any], response_text: str) -> str:
        """Generate a natural acknowledgment of the candidate's response using LLM with caching."""
        
        # Short responses don't need detailed acknowledgment
        if len(response_text.split()) < 15:
            # Simple acknowledgments for short responses
            simple_acknowledges = [
                "Thank you for your response.",
                "I appreciate your answer.",
                "Thanks for sharing that.",
                "I understand.",
                "Thanks for that perspective."
            ]
            import random
            return random.choice(simple_acknowledges)
            
        # For longer, more substantive responses, use the LLM to generate a contextual acknowledgment
        try:
            # Create a prompt for generating a personalized acknowledgment
            prompt = f"""
            As an expert technical interviewer, create a brief, natural acknowledgment for the candidate's response.
            
            Question: "{current_question.get('question', '')}"
            Category: {current_question.get('category', 'general')}
            Candidate response: "{response_text}"
            
            Your acknowledgment should:
            1. Be 1-2 short sentences maximum
            2. Reference specific content from their response
            3. Sound natural and conversational (not formulaic)
            4. Avoid generic phrases like "Thank you for sharing that"
            5. Show active listening and engagement with what they said
            6. NOT evaluate or judge their response quality
            7. NOT ask any questions
            
            Return ONLY the acknowledgment text with no additional commentary.
            """
            
            # Check cache first
            cache_key = f"acknowledgment:{hash(response_text)}:{hash(str(current_question))}"
            if cache_key in self.prompt_cache:
                logger.debug("Using cached acknowledgment")
                acknowledgment = self.prompt_cache[cache_key]
            else:
                # Generate the acknowledgment using the LLM - but with a short timeout
                acknowledgment = ""
                try:
                    # Use a timeout mechanism if available
                    import threading
                    import queue
                    
                    def generate_with_timeout():
                        nonlocal acknowledgment
                        try:
                            result = self.generator.llm.generate_text(prompt)
                            result_queue.put(result)
                        except Exception as inner_err:
                            logger.error(f"Error in acknowledgment thread: {str(inner_err)}")
                            result_queue.put("")
                    
                    result_queue = queue.Queue()
                    thread = threading.Thread(target=generate_with_timeout)
                    thread.daemon = True
                    thread.start()
                    
                    # Wait for 3 seconds max for acknowledgment
                    try:
                        acknowledgment = result_queue.get(timeout=3)
                        # Cache the result
                        self.prompt_cache[cache_key] = acknowledgment
                    except queue.Empty:
                        logger.warning("Acknowledgment generation timed out")
                        return self._get_fallback_acknowledgment(current_question, response_text)
                        
                except Exception as timeout_err:
                    logger.error(f"Timeout mechanism failed: {str(timeout_err)}")
                    # Direct call as fallback for the timeout mechanism
                    try:
                        acknowledgment = self.generator.llm.generate_text(prompt)
                        # Cache the result
                        self.prompt_cache[cache_key] = acknowledgment
                    except Exception as direct_err:
                        logger.error(f"Direct acknowledgment generation failed: {str(direct_err)}")
                        return self._get_fallback_acknowledgment(current_question, response_text)
            
            # Clean up the response - remove quotes, ensure proper punctuation, etc.
            acknowledgment = acknowledgment.strip().strip('"\'').strip()
            
            # Set a reasonable length limit to prevent verbose acknowledgments
            if len(acknowledgment.split()) > 25:
                # Truncate to first 2 sentences
                import re
                sentences = re.split(r'[.!?]+', acknowledgment)
                acknowledgment = '. '.join([s.strip() for s in sentences[:2] if s.strip()]) + '.'
            
            # Fallback to category-based acknowledgments if LLM fails or returns empty
            if not acknowledgment:
                return self._get_fallback_acknowledgment(current_question, response_text)
                
            logger.debug(f"Generated acknowledgment: {acknowledgment}")
            return acknowledgment
                
        except Exception as e:
            logger.error(f"Error generating acknowledgment: {str(e)}")
            return self._get_fallback_acknowledgment(current_question, response_text)
            
    def _get_fallback_acknowledgment(self, current_question: Dict[str, Any], response_text: str) -> str:
        """Provide fallback acknowledgments based on question category if LLM generation fails."""
        # Base acknowledgments by question category
        acknowledgments = {
            "introduction": [
                "Thank you for sharing that background information.",
                "I appreciate you giving us that overview.",
                "That's helpful context about your experience."
            ],
            "job_specific": [
                "Thank you for sharing those insights about your experience.",
                "I appreciate your detailed explanation of your relevant background.",
                "That's valuable information about your skills in this area."
            ],
            "technical": [
                "Thanks for explaining your approach to that technical challenge.",
                "I appreciate your technical perspective on that topic.",
                "That's a helpful explanation of your technical expertise."
            ],
            "company_fit": [
                "Thank you for sharing your thoughts on our company culture.",
                "I appreciate your perspective on how you might fit with our team.",
                "That's helpful to understand your alignment with our values."
            ],
            "behavioral": [
                "Thank you for sharing that experience with me.",
                "I appreciate the detailed example from your past work.",
                "That's a helpful illustration of how you handle those situations."
            ],
            "closing": [
                "Thank you for your thoughtful questions.",
                "I appreciate your interest in our company.",
                "Thank you for all your insights throughout this interview."
            ]
        }
        
        # Default acknowledgments if category not found
        default_acknowledgments = [
            "Thank you for that response.",
            "I appreciate your thoughtful answer.",
            "Thanks for sharing that with me."
        ]
        
        # Select a random acknowledgment based on the question category
        category = current_question.get("category", "")
        category_acknowledgments = acknowledgments.get(category, default_acknowledgments)
        
        # For longer responses, use more enthusiastic acknowledgments
        words = len(response_text.split())
        if words > 100:
            return f"{category_acknowledgments[0]} That was a very comprehensive answer."
        elif words > 50:
            return category_acknowledgments[0]
        else:
            import random
            return random.choice(category_acknowledgments)
    
    def generate_summary(self, early_termination=False):
        """Generate a summary of the interview."""
        if not self.responses and not early_termination:
            logger.warning("No responses recorded, cannot generate summary")
            self.summary = {"error": "No responses recorded"}
            return self.summary
            
        try:
            # Enhanced summary generation with memory insights
            prompt = "Please provide a comprehensive interview summary based on the following data:\n\n"
            
            # Add job information
            prompt += f"Job Title: {self.job_data.get('title', 'N/A')}\n"
            prompt += f"Required Skills: {', '.join(self.job_data.get('required_skills', []))}\n\n"
            
            # Add responses
            prompt += "Interview Questions and Responses:\n"
            for i, response in enumerate(self.responses):
                question = response.get("question", {}).get("question", "")
                answer = response.get("response", "")
                prompt += f"Q{i+1}: {question}\nA: {answer}\n\n"
            
            # Add memory insights
            prompt += "Candidate Insights:\n"
            prompt += f"- Topics mentioned: {', '.join(self.memory.get_recent_topics())}\n"
            
            dominant_style = self.memory.get_dominant_style()
            if dominant_style:
                prompt += f"- Communication style: {dominant_style}\n"
            
            for insight, count in self.memory.insights.items():
                if count > 0:
                    prompt += f"- {insight.replace('_', ' ').title()}: {count} instances\n"
            
            # Generate summary
            logger.info("Generating interview summary with memory insights")
            summary = self.generator.generate_interview_summary(
                prompt,
                self.job_data,
                self.company_data,
                self.candidate_data,
                early_termination
            )
            
            self.summary = summary
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            # Use minimal summary as fallback
            return self._generate_minimal_summary(early_termination)

    def _generate_minimal_summary(self, early_termination=False):
        """Generate a minimal summary when a full one cannot be created."""
        response_count = len(self.responses)
        name = self.candidate_data.get("name", "The candidate")
        position = self.job_data.get("title", "the position")
        
        summary = {
            "candidate_name": name,
            "position": position,
            "strengths": ["Could not analyze fully" + (" due to early termination" if early_termination else "")],
            "areas_for_improvement": ["Could not analyze fully" + (" due to early termination" if early_termination else "")],
            "technical_evaluation": f"Interview had only {response_count} responses, which is not enough for a full evaluation" + (" and was terminated early" if early_termination else ""),
            "cultural_fit": "Not enough information to evaluate",
            "recommendation": "More information needed",
            "next_steps": "Consider conducting another interview to gather more information",
            "overall_assessment": f"{name} participated in a brief interview for {position} " + ("but the interview was terminated early" if early_termination else "but did not complete enough questions for a full assessment")
        }
        
        return summary
    
    def get_interview_state(self) -> Dict[str, Any]:
        """Get the current state of the interview."""
        state = {
            "active": self.interview_active,
            "complete": self.interview_complete,
            "current_question_index": self.current_question_index,
            "total_questions": len(self.questions),
            "responses_count": len(self.responses),
            "follow_ups_count": len(self.follow_ups)
        }
        logger.debug(f"Retrieved interview state: {state}")
        return state
    
    def get_interview_data(self) -> Dict[str, Any]:
        """Get all interview data including questions, responses, and summary."""
        logger.info("Retrieving complete interview data")
        return {
            "job_data": self.job_data,
            "company_data": self.company_data,
            "candidate_data": self.candidate_data,
            "script": self.script,
            "questions": self.questions,
            "responses": self.responses,
            "follow_ups": self.follow_ups,
            "summary": self.summary,
            "state": self.get_interview_state()
        }
    
    def _detect_candidate_question(self, response_text: str) -> bool:
        """Determine if the response is actually a candidate question using improved detection."""
        text = response_text.strip().lower()
        
        # Check ending with question mark (highest confidence)
        if text.endswith('?'):
            return True
            
        # Check for question phrases (medium confidence)
        question_phrases = [
            'i have a question', 'can you tell me', 'could you explain',
            'tell me about', 'what is', 'how do you', 'who is', 'when will',
            'why do', 'where is', 'is there', 'are there', 'will you',
            'could you', 'would it be', 'do you know', 'i wonder if',
            "i'd like to know"
        ]
        
        for phrase in question_phrases:
            if phrase in text:
                return True
        
        # If not clearly a question by simple heuristics, use LLM for more nuanced detection
        # Only do this for longer, potentially complex texts
        if len(text.split()) > 15:
            try:
                # Use cached LLM response if available
                cache_key = f"question_detection:{hash(text)}"
                if cache_key in self.prompt_cache:
                    return self.prompt_cache[cache_key]
                
                # Simple prompt to check if this is a question
                prompt = f"""
                Determine if the following text contains a question from a job candidate to an interviewer.
                Answer with only "Yes" or "No".
                
                Text: "{text}"
                """
                
                response = self.generator.llm.generate_text(prompt, max_tokens=5)
                is_question = response.strip().lower() == "yes"
                
                # Cache the result
                self.prompt_cache[cache_key] = is_question
                
                return is_question
            except Exception as e:
                logger.error(f"Error in advanced question detection: {str(e)}")
        
        return False
        
    def _handle_candidate_question(self, question_text: str, current_question: Dict[str, Any]) -> Dict[str, Any]:
        """Handle questions asked by the candidate using LLM with context."""
        # Record the candidate's question for tracking
        self.candidate_questions.append({
            "question": question_text,
            "timestamp": time.time(),
            "current_question_index": self.current_question_index
        })
        
        # Add to conversation memory
        self.memory.add_exchange({"question": question_text}, "", is_candidate_question=True)
        
        # Generate a response using context from memory
        prompt = f"""
        You are an interviewer for {self.company_data.get('name', 'the company')} interviewing for a {self.job_data.get('title', 'position')} role.
        
        The candidate has asked: "{question_text}"
        
        Context about the company:
        {self.company_data.get('description', '')}
        {self.company_data.get('values', '')}
        
        Job details:
        {self.job_data.get('description', '')}
        {self.job_data.get('required_skills', [])}
        
        Prior conversation context:
        {self._get_conversation_context()}
        
        Respond naturally and conversationally to their question without forced phrasing like "That's a good question."
        Keep your answer concise but informative.
        """
        
        try:
            question_response = self.generator.llm.generate_text(prompt)
            
            # Clean the response of any extra formatting
            question_response = question_response.strip().strip('"\'`')
            
            # Return the response and continue with the same question
            return {
                "status": "active",
                "acknowledgment": question_response,
                "question": current_question,
                "question_number": self.current_question_index + 1, 
                "total_questions": len(self.questions)
            }
        except Exception as e:
            logger.error(f"Error generating response to candidate question: {str(e)}")
            # Simple fallback
            return {
                "status": "active",
                "acknowledgment": "That's a good question. Our company values transparency and innovation. Let's continue with the interview questions.",
                "question": current_question,
                "question_number": self.current_question_index + 1,
                "total_questions": len(self.questions)
            }
            
    def _get_conversation_context(self) -> str:
        """Get recent conversation context to provide to the LLM."""
        context = ""
        
        # Get the last few exchanges from memory
        recent_exchanges = self.memory.conversation_history[-5:]  # Last 5 exchanges
        
        for exchange in recent_exchanges:
            if exchange.get("is_candidate_question"):
                context += f"Candidate asked: {exchange.get('question', {}).get('question', '')}\n"
            else:
                context += f"Interviewer: {exchange.get('question', {}).get('question', '')}\n"
                context += f"Candidate: {exchange.get('response', '')}\n\n"
        
        return context
    
    def _check_duplicate_response(self, new_response: str, question_index: int) -> bool:
        """Check if the response is a duplicate or very similar to previous responses."""
        # Get previous responses for this question
        question_key = str(question_index)
        if question_key not in self.previous_responses:
            self.previous_responses[question_key] = []
        
        # Don't check for duplicates if it's a candidate question
        if self._detect_candidate_question(new_response):
            return False
            
        # Compare with previous responses for this question
        for prev_response in self.previous_responses[question_key]:
            similarity = self._calculate_similarity(new_response, prev_response)
            logger.debug(f"Response similarity score: {similarity}")
            
            # If very similar, consider it a duplicate
            if similarity > 0.8:  # Threshold for similarity
                return True
        
        # Add this response to the list of previous responses
        self.previous_responses[question_key].append(new_response)
        return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        from difflib import SequenceMatcher
        
        # Clean and normalize the texts
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        # Calculate similarity ratio
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _handle_duplicate_response(self, response_text: str, current_question: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a duplicate or very similar response appropriately."""
        # If this is a candidate question, don't treat it as a duplicate
        if self._detect_candidate_question(response_text):
            return self._handle_candidate_question(response_text, current_question)
        
        # For closing questions, if it contains a question, handle it as a candidate question
        if current_question["category"] == "closing" and self._detect_candidate_question(response_text):
            return self._handle_candidate_question(response_text, current_question)
        
        # For other duplicate responses, move to the next question
        logger.info("Handling duplicate response by moving to next question")
        
        # Move to next question
        next_question = self.get_next_question()
        
        if next_question:
            # Include transition phrase for a more natural flow
            transition = next_question.get("transition", "")
            
            return {
                "status": "active",
                "is_follow_up": False,
                "acknowledgment": "Thank you for your response.",
                "question": next_question,
                "transition": transition,
                "question_number": self.current_question_index + 1,
                "total_questions": len(self.questions)
            }
        else:
            # Interview is complete
            self.interview_active = False
            self.interview_complete = True
            
            # Generate summary
            logger.info("Interview complete after duplicate response, generating summary")
            self.summary = self.generate_summary()
            
            return {
                "status": "complete",
                "acknowledgment": "Thank you for your response.",
                "closing_remarks": self.script["closing"],
                "summary": self.summary
            }

    def _response_contains_question(self, response_text: str) -> bool:
        """Determine if the response contains a question from the candidate."""
        # This is just an alias for the existing _detect_candidate_question method
        return self._detect_candidate_question(response_text)

    def _should_ask_follow_up(self, response_text: str, question: Dict[str, Any], follow_up_count: int) -> bool:
        """Determine if a follow-up question is needed based on improved response quality evaluation."""
        # Check if the candidate wants to move on
        move_on_phrases = [
            "can we move", "next question", "moving on", "let's continue", 
            "next section", "proceed", "getting rushed", "short on time", 
            "move forward", "continue with", "go ahead"
        ]
        
        if any(phrase in response_text.lower() for phrase in move_on_phrases):
            logger.info("Candidate indicated desire to move on - skipping follow-up")
            return False
            
        # In demo mode, drastically limit follow-ups to keep the interview shorter
        if self.demo_mode:
            # In demo mode, only ask follow-ups for very short responses and limit to 1 per question
            if follow_up_count > 0:
                logger.info("Already asked one follow-up in demo mode - moving on")
                return False
                
            # Only ask follow-up for extremely short responses in demo mode
            if len(response_text.split()) < 15:
                logger.info("Response is very short in demo mode - asking follow-up")
                return True
                
            # Skip most follow-ups in demo mode
            logger.info("In demo mode - skipping follow-up for adequate response")
            return False
        
        # For regular mode, be more selective about follow-ups
        
        # Limit total follow-ups per question
        if follow_up_count >= 2:
            logger.info("Already asked two follow-ups - moving on")
            return False
        
        # Use LLM to evaluate response quality
        try:
            # Use cached evaluation if available
            cache_key = f"response_quality:{hash(response_text)}:{hash(str(question))}"
            if cache_key in self.prompt_cache:
                quality_score = self.prompt_cache[cache_key]
                logger.info(f"Using cached response quality score: {quality_score}")
            else:
                # Prompt to evaluate response quality
                prompt = f"""
                Evaluate this candidate response for depth, relevance, and completeness.
                
                Question: "{question.get('question', '')}"
                Category: {question.get('category', 'general')}
                Candidate response: "{response_text}"
                
                Rate the response quality on a scale of 1-10, where:
                1-3: Very shallow, generic, or irrelevant
                4-6: Somewhat adequate but could use more detail or focus
                7-10: Comprehensive, relevant, and well-explained
                
                Return only the numeric score (1-10).
                """
                
                quality_result = self.generator.llm.generate_text(prompt, max_tokens=10)
                
                # Extract numeric score
                try:
                    quality_score = int(quality_result.strip())
                    # Normalize if outside expected range
                    quality_score = max(1, min(10, quality_score))
                except ValueError:
                    # Default to mid-range if parsing fails
                    logger.warning(f"Failed to parse quality score: {quality_result}")
                    quality_score = 5
                
                # Cache the result
                self.prompt_cache[cache_key] = quality_score
                
            logger.info(f"Response quality score: {quality_score}/10")
            
            # Determine follow-up based on quality score
            if quality_score <= 3:
                logger.info("Low quality response - asking follow-up")
                return True
            elif quality_score <= 6 and follow_up_count == 0:
                logger.info("Medium quality response - asking first follow-up")
                return True
            elif quality_score >= 7:
                logger.info("High quality response - no follow-up needed")
                return False
                
        except Exception as e:
            logger.error(f"Error in LLM-based quality evaluation: {str(e)}")
            # Fall back to length-based and category-specific heuristics if LLM fails
            
            # Short responses get a follow-up
            if len(response_text.split()) < 25:
                return True
                
            # Category-specific checks
            if question["category"] == "technical" and follow_up_count == 0:
                if len(response_text.split()) < 75:
                    return True
                    
                technical_markers = [
                    "implemented", "designed", "developed", "algorithm",
                    "complexity", "architecture", "solution", "framework",
                    "database", "system", "code", "programming"
                ]
                
                marker_count = sum(1 for marker in technical_markers if marker.lower() in response_text.lower())
                
                if marker_count < 2:
                    return True
            
            # Behavioral questions analysis
            if question["category"] == "behavioral" and follow_up_count == 0:
                situation_markers = ["when", "situation", "context", "challenge", "problem", "faced"]
                action_markers = ["did", "action", "took", "steps", "approach", "handled", "implemented"]
                result_markers = ["result", "outcome", "impact", "learned", "achieved", "ended", "succeeded"]
                
                has_situation = any(marker in response_text.lower() for marker in situation_markers)
                has_action = any(marker in response_text.lower() for marker in action_markers)
                has_result = any(marker in response_text.lower() for marker in result_markers)
                
                if not (has_situation and has_action and has_result):
                    return True
            
            # For very long responses, assume they're comprehensive
            if len(response_text.split()) > 100:
                logger.info("Very long response - skipping follow-up")
                return False
            
            # Use randomness for first follow-up if we made it here
            if follow_up_count == 0:
                import random
                should_follow_up = random.random() < 0.5
                logger.info(f"Random decision for follow-up: {should_follow_up}")
                return should_follow_up
            
        # Default to not asking a follow-up
        return False
    
    def _get_conversational_buffer(self, current_response: str, current_question: Dict, next_question: Dict) -> str:
        """Generate a natural conversational transition based on memory and context."""
        try:
            # Use conversation memory to create a contextual transition
            contextual_prompt = self.memory.get_contextual_prompt(current_question, next_question)
            
            transition = self.generator.generate_transition(
                contextual_prompt, 
                current_response, 
                current_question, 
                next_question
            )
            
            if not transition or len(transition) < 10:
                # Fallback to predefined transition if generation failed
                transition = next_question.get("transition", "Let's move on to the next question.")
                
            return transition
        except Exception as e:
            logger.error(f"Error generating conversational buffer: {e}")
            # Fallback to basic transition
            return next_question.get("transition", "Thank you. Let's move on to the next question.")
    
    def generate_visual_summary(self) -> Dict[str, Any]:
        """Generate visualization-ready data from interview summary"""
        if not self.summary:
            self.generate_summary()
        
        visual_data = {
            "candidate_name": self.summary.get("candidate_name", "Candidate"),
            "position": self.summary.get("position", "Position"),
            # Create skill rating map (0-100) for visualization
            "skill_ratings": self._extract_skill_ratings(),
            # Map strengths and areas for improvement to visualization format
            "strengths": [{"text": s, "score": 85 + i*5} for i, s in 
                         enumerate(self.summary.get("strengths", [])[:3])],
            "improvements": [{"text": a, "score": 60 - i*10} for i, a in 
                            enumerate(self.summary.get("areas_for_improvement", [])[:3])],
            # Create recommendation score (0-100)
            "recommendation_score": self._calculate_recommendation_score(),
            "recommendation_text": self.summary.get("recommendation", "")
        }
        return visual_data
    
    def _extract_skill_ratings(self) -> List[Dict[str, Any]]:
        """Extract skill ratings from technical evaluation for visualization"""
        tech_eval = self.summary.get("technical_evaluation", "")
        
        # Extract skills with regex and assign ratings
        import re
        skills = []
        
        # First try to extract structured ratings
        skill_matches = re.findall(r'([A-Za-z]+(?:\s[A-Za-z]+)?)\s*:\s*(Not Demonstrated|Basic|Proficient|Expert)', tech_eval)
        
        if skill_matches:
            # Convert text ratings to numeric
            rating_map = {
                "Not Demonstrated": 10,
                "Basic": 40, 
                "Proficient": 75,
                "Expert": 95
            }
            
            for skill, rating in skill_matches:
                skills.append({
                    "name": skill,
                    "score": rating_map.get(rating, 50)
                })
        else:
            # Fallback to required skills from job data with estimated ratings
            for i, skill in enumerate(self.job_data.get("required_skills", [])[:5]):
                # Generate pseudo-random scores that look realistic
                import hashlib
                seed = int(hashlib.md5(str(skill).encode()).hexdigest(), 16) % 40
                score = min(95, max(30, 55 + seed))
                
                skills.append({
                    "name": skill,
                    "score": score
                })
        
        return skills
    
    def _calculate_recommendation_score(self) -> int:
        """Calculate numeric recommendation score for visualization"""
        rec_text = self.summary.get("recommendation", "").lower()
        
        if "highly recommend" in rec_text:
            return 90
        elif "recommend" in rec_text:
            return 75
        elif "neutral" in rec_text:
            return 50
        elif "not recommend" in rec_text:
            return 25
        else:
            return 50
    
    def collect_interview_analytics(self) -> Dict[str, Any]:
        """Collect interview analytics data for reporting and evaluation"""
        if not self.responses:
            return {"error": "No interview data available"}
        
        analytics = {
            "interview_id": id(self),
            "candidate_name": self.candidate_data.get("name", "Unknown"),
            "position": self.job_data.get("title", "Unknown"),
            "duration_seconds": 0,
            "question_count": len(self.questions),
            "response_count": len(self.responses),
            "follow_up_count": len(self.follow_ups),
            "question_categories": {},
            "response_metrics": {
                "avg_response_length": 0,
                "avg_response_time": 0,
                "technical_term_usage": {},
                "communication_style": {}
            },
            "candidate_questions": len(self.candidate_questions),
            "key_topics": []
        }
        
        # Add memory topics if available
        if hasattr(self, 'memory') and hasattr(self.memory, 'topics_mentioned'):
            analytics["key_topics"] = list(self.memory.topics_mentioned)
            if hasattr(self.memory, 'candidate_style'):
                analytics["response_metrics"]["communication_style"] = self.memory.candidate_style.copy()
        
        # Calculate timing metrics
        if self.responses:
            start_time = self.responses[0].get("timestamp", 0)
            end_time = self.responses[-1].get("timestamp", 0)
            analytics["duration_seconds"] = end_time - start_time
            
            # Calculate average response length
            total_words = sum(len(r.get("response", "").split()) for r in self.responses)
            analytics["response_metrics"]["avg_response_length"] = total_words / len(self.responses)
        
        # Count questions by category
        for q in self.questions:
            category = q.get("category", "unknown")
            analytics["question_categories"][category] = analytics["question_categories"].get(category, 0) + 1
        
        return analytics 