from typing import List, Dict, Any, Optional
import logging
import json
import re
from .llm_interface import LLMInterface
import os
from .llm_adapter import get_llm_adapter

logger = logging.getLogger(__name__)

class InterviewGenerator:
    """Handles generation of interview scripts, questions, and evaluations."""
    
    def __init__(self, llm_interface: LLMInterface):
        """Initialize with an LLM interface for text generation."""
        self.llm = llm_interface
        logger.info("Initialized InterviewGenerator")
        
    def generate_interview_script(self, job_data: Dict[str, Any], 
                                  company_data: Dict[str, Any], 
                                  candidate_data: Dict[str, Any], 
                                  demo_mode: bool = False) -> Dict[str, Any]:
        """Generate an interview script using the LLM."""
        logger.info("Generating interview script")
        
        try:
            # Create prompt for the LLM
            prompt = self._create_script_generation_prompt(job_data, company_data, candidate_data, demo_mode)
            
            # Generate script using the LLM
            try:
                response = self.llm.generate_text(prompt)
                logger.info("Successfully received response from LLM")
                
                # Try to parse the response into a structured script
                try:
                    script = self._parse_script_response(response)
                    logger.info("Successfully parsed interview script")
                    return script
                except ValueError as parse_error:
                    logger.error(f"Error parsing script response: {str(parse_error)}")
                    raise
            except Exception as llm_error:
                logger.error(f"Error generating text from LLM: {str(llm_error)}")
                raise
        except Exception as e:
            logger.error(f"Error generating interview script: {str(e)}")
            logger.exception("Exception details:")
            
            # Generate a fallback script
            logger.info("Generating fallback interview script")
            return self._generate_fallback_script(job_data, demo_mode)
    
    def _create_script_generation_prompt(self, job_data: Dict[str, Any], 
                                        company_data: Dict[str, Any], 
                                        candidate_data: Dict[str, Any],
                                        demo_mode: bool = False) -> str:
        """Create a prompt for generating the interview script."""
        
        job_title = job_data.get('title', 'the position')
        company_name = company_data.get('name', 'our company')
        
        # Set question counts based on demo mode
        job_specific_count = 2 if demo_mode else 5
        technical_count = 1 if demo_mode else "3-5"
        company_fit_count = 1 if demo_mode else "2-3"
        behavioral_count = 1 if demo_mode else "3-4"
        
        prompt = f"""
        You are an AI interviewer for {company_name}. You need to conduct an interview for the {job_title} position.
        
        Job Description:
        {job_data.get('description', 'Not provided')}
        
        Required Skills:
        {job_data.get('required_skills', 'Not provided')}
        
        Company Information:
        {company_data.get('description', 'Not provided')}
        Company Values: {company_data.get('values', 'Not provided')}
        
        Candidate Information:
        Name: {candidate_data.get('name', 'the candidate')}
        Experience: {candidate_data.get('experience', 'Not provided')}
        Background: {candidate_data.get('background', 'Not provided')}
        
        Create a professional interview script with:
        1. A personalized introduction welcoming the candidate
        2. A set of interview questions categorized as:
           - Job-specific questions ({job_specific_count} questions)
           - Technical questions ({technical_count} questions)
           - Company fit questions ({company_fit_count} questions)
           - Behavioral questions ({behavioral_count} questions)
        3. A professional closing statement
        
        For each question, include:
        - The question text
        - The purpose of asking this question
        - What to look for in a good answer
        
        IMPORTANT: Use a diverse range of question formats to make the interview feel natural and varied. Include a mix of:
        - Direct knowledge questions: "What is your understanding of...?"
        - Skill assessment questions: "How would you implement...?"
        - Hypothetical scenarios: "Imagine you're faced with [scenario], what would your approach be?"
        - Opinion-based questions: "What do you think about...?"
        - Experience-sharing questions: "Tell me about a time when..." (use this format sparingly)
        - Problem-solving questions: "How would you solve...?"
        - Self-assessment questions: "What would you consider your biggest strength in...?"
        
        Avoid falling into repetitive patterns like starting every question with "Can you share an example of..." or "Could you tell me about a time when...". Make each question distinct in its structure and wording.
        
        Format the response as JSON with the following structure:
        ```json
        {{
            "introduction": "...",
            "questions": {{
                "job_specific": [
                    {{"question": "...", "purpose": "...", "good_answer_criteria": "..."}}
                ],
                "technical": [
                    {{"question": "...", "purpose": "...", "good_answer_criteria": "..."}}
                ],
                "company_fit": [
                    {{"question": "...", "purpose": "...", "good_answer_criteria": "..."}}
                ],
                "behavioral": [
                    {{"question": "...", "purpose": "...", "good_answer_criteria": "..."}}
                ]
            }},
            "closing": "..."
        }}
        ```
        """
        return prompt
    
    def _parse_script_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into a structured interview script."""
        logger.info("Successfully received response from LLM")
        logger.debug(f"Raw LLM response length: {len(response)} chars")
        
        try:
            # First, look for JSON in the response
            import json
            
            # Check for content in code blocks
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                logger.debug("Found JSON in code block")
                json_str = json_match.group(1)
            else:
                # Check if the entire response looks like it might be JSON
                json_str = response.strip()
                if not (json_str.startswith('{') and json_str.endswith('}')):
                    logger.warning("No JSON structure found in response, using full text")
            
            # Pre-process to fix common JSON issues
            logger.info("Attempting to fix potential JSON errors")
            json_str = self._fix_json_string(json_str)
            
            # Try to parse the JSON
            script = json.loads(json_str)
            logger.info("Successfully parsed JSON")
            
            # If we get here, we have valid JSON.
            # Check for required fields and add them if missing
            required_fields = ['introduction', 'questions', 'closing']
            for field in required_fields:
                if field not in script:
                    logger.warning(f"Missing required field '{field}' in script")
                    if field == 'introduction':
                        script['introduction'] = "Welcome to your interview. I'm excited to learn more about your background and experience."
                    elif field == 'questions':
                        script['questions'] = {}
                    elif field == 'closing':
                        script['closing'] = "Thank you for your time today. We'll be in touch regarding next steps."
            
            # Check for required question categories
            question_categories = ['job_specific', 'technical', 'company_fit', 'behavioral']
            if 'questions' in script:
                for category in question_categories:
                    if category not in script['questions']:
                        logger.warning(f"Missing question category '{category}' in script")
                        
                        # Add at least one question per missing category
                        if category == 'job_specific':
                            script['questions'][category] = [{
                                "question": "Could you tell me about your relevant experience for this position?",
                                "purpose": "To understand the candidate's background",
                                "good_answer_criteria": "Specific examples that demonstrate required skills"
                            }]
                        elif category == 'technical':
                            script['questions'][category] = [{
                                "question": "Can you describe a technical challenge you faced recently and how you resolved it?",
                                "purpose": "To assess problem-solving abilities",
                                "good_answer_criteria": "Clear problem description and effective solution"
                            }]
                        elif category == 'company_fit':
                            script['questions'][category] = [{
                                "question": "What interests you most about working with our company?",
                                "purpose": "To gauge cultural fit",
                                "good_answer_criteria": "Alignment with company values"
                            }]
                        elif category == 'behavioral':
                            script['questions'][category] = [{
                                "question": "Tell me about a time when you had to adapt to a significant change.",
                                "purpose": "To assess adaptability",
                                "good_answer_criteria": "Positive attitude toward change, specific actions taken"
                            }]
                        else:
                            script['questions'][category] = []
            
            logger.info("Successfully parsed interview script")
            return script
            
        except Exception as e:
            logger.error(f"Error parsing script response: {str(e)}")
            logger.warning("Falling back to default interview script")
            
            # Generate a fallback script since parsing failed
            return self._generate_fallback_script(self.job_data, self.demo_mode)
    
    def _fix_json_string(self, json_str: str) -> str:
        """Apply common fixes to malformed JSON strings."""
        if not json_str:
            return "{}"
        
        # First try to parse as-is
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError as e:
            logger.debug(f"JSON error detected: {str(e)}")
        
        # Try to extract JSON from markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', json_str, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        
        # Apply targeted fixes for common errors
        try:
            # Fix unquoted property names (without using look-behind)
            json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)', r'\1"\2"\3', json_str)
            
            # Remove trailing commas
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            # Fix unescaped quotes in strings
            json_str = re.sub(r'(?<!\\)"([^"]*?)(?<!\\)"', lambda m: '"' + m.group(1).replace('"', '\\"') + '"', json_str)
            
            # Try parsing again
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError as e:
            logger.debug(f"Error after initial fixes: {str(e)}")
        
        # If still invalid, try more aggressive fixes
        try:
            # Remove any non-JSON characters
            json_str = re.sub(r'[^\x20-\x7E]', '', json_str)
            
            # Ensure the string starts with { and ends with }
            if not json_str.strip().startswith('{'):
                json_str = '{' + json_str
            if not json_str.strip().endswith('}'):
                json_str = json_str + '}'
            
            # Try parsing one final time
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError as e:
            logger.error(f"Failed to fix JSON string: {str(e)}")
            # If all else fails, return a minimal valid JSON structure
            return '{"error": "Failed to parse JSON response"}'
    
    def _aggressively_fix_json(self, json_str: str) -> str:
        """More aggressive JSON fixing for severely malformed responses."""
        import re
        import json
        
        # First try our standard fixes
        json_str = self._fix_json_string(json_str)
        
        # Try to identify the specific error location
        try:
            json.loads(json_str)
            return json_str  # If no error, return as is
        except json.JSONDecodeError as e:
            error_line = e.lineno
            error_col = e.colno
            error_msg = str(e)
            logger.warning(f"JSON error at line {error_line}, column {error_col}: {error_msg}")
            
            # Extract all lines
            lines = json_str.split('\n')
            
            # Handle the line 2 column 5 issue which is very common
            if error_line == 2 and error_col == 5:
                logger.debug("Targeted fix for line 2 column 5 error")
                if len(lines) >= 2:
                    # Try simply quoting what looks like a property name
                    match = re.match(r'(\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)(.*)', lines[1])
                    if match:
                        indent, prop_name, colon, rest = match.groups()
                        lines[1] = f'{indent}"{prop_name}"{colon}{rest}'
                    json_str = '\n'.join(lines)
            
            # If the error is "Expecting ',' delimiter", try to insert a comma
            elif "Expecting ',' delimiter" in error_msg and error_line <= len(lines):
                problematic_line = lines[error_line - 1]
                # Insert a comma at the error position
                fixed_line = problematic_line[:error_col] + ',' + problematic_line[error_col:]
                lines[error_line - 1] = fixed_line
                json_str = '\n'.join(lines)
            
            # If the error is "Expecting property name", try to fix the format
            elif "Expecting property name" in error_msg and error_line <= len(lines):
                problematic_line = lines[error_line - 1]
                # Look for an unquoted property name pattern
                match = re.search(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)', problematic_line)
                if match:
                    prefix, prop_name, suffix = match.groups()
                    fixed_line = problematic_line.replace(f"{prefix}{prop_name}{suffix}", f'{prefix}"{prop_name}"{suffix}')
                    lines[error_line - 1] = fixed_line
                else:
                    # If we can't find a property pattern, use a generic fix
                    fixed_line = problematic_line[:error_col] + '"missing_property":' + problematic_line[error_col:]
                    lines[error_line - 1] = fixed_line
                
                json_str = '\n'.join(lines)
        
        # Try one last general approach - quote all property-like patterns
        try:
            json.loads(json_str)
            return json_str
        except:
            # Quote all patterns that look like property names
            json_str = re.sub(r'(?<=[{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r' "\1":', json_str)
            
            try:
                # See if it's valid now
                json.loads(json_str)
                return json_str
            except:
                # One last approach: try a complete structural rebuild
                if json_str.strip().startswith('{') and json_str.strip().endswith('}'):
                    # Try extracting key sections we can identify
                    intro_match = re.search(r'"introduction"\s*:\s*"([^"\\]*(\\.[^"\\]*)*)"\s*,?', json_str)
                    questions_start = json_str.find('"questions"')
                    closing_match = re.search(r'"closing"\s*:\s*"([^"\\]*(\\.[^"\\]*)*)"\s*}?', json_str)
                    
                    if intro_match and closing_match:
                        intro_text = intro_match.group(1)
                        closing_text = closing_match.group(1)
                        
                        # Create a minimal valid structure
                        min_json = (
                            '{\n'
                            f'    "introduction": "{intro_text}",\n'
                            '    "questions": {\n'
                            '        "job_specific": [],\n'
                            '        "technical": [],\n'
                            '        "company_fit": [],\n'
                            '        "behavioral": []\n'
                            '    },\n'
                            f'    "closing": "{closing_text}"\n'
                            '}'
                        )
                        
                        try:
                            json.loads(min_json)
                            logger.warning("Created minimal valid JSON from extracted sections")
                            return min_json
                        except:
                            pass
        
        # If all else fails
        logger.error("All JSON fixing attempts failed, falling back to minimal valid structure")
        return '{}'
    
    def _generate_fallback_script(self, job_data: Dict[str, Any], demo_mode: bool = False) -> Dict[str, Any]:
        """Generate a basic fallback interview script if the LLM fails."""
        logger.info("Generating fallback interview script")
        
        job_title = job_data.get('title', 'the position')
        
        # Basic fallback script
        script = {
            "introduction": f"Hello and welcome to the interview for {job_title}. Thank you for taking the time to speak with us today.",
            "questions": {
                "job_specific": [
                    {
                        "question": f"Could you tell me about your experience related to {job_title}?",
                        "purpose": "To understand the candidate's relevant experience",
                        "good_answer_criteria": "Specific examples of relevant work"
                    }
                ],
                "technical": [
                    {
                        "question": "What technical skills do you bring to this role?",
                        "purpose": "To assess technical capabilities",
                        "good_answer_criteria": "Relevant technical skills with examples"
                    }
                ],
                "company_fit": [
                    {
                        "question": "What do you know about our company?",
                        "purpose": "To assess company research",
                        "good_answer_criteria": "Knowledge of company and its values"
                    }
                ],
                "behavioral": [
                    {
                        "question": "Tell me about a challenging situation you faced at work and how you handled it.",
                        "purpose": "To assess problem-solving abilities",
                        "good_answer_criteria": "Clear problem description, actions taken, and results"
                    }
                ]
            },
            "closing": "Thank you for your time today. We'll be in touch regarding next steps."
        }
        
        # If in demo mode, don't add the second job-specific question
        if not demo_mode:
            script["questions"]["job_specific"].append({
                "question": "What interests you most about this position?",
                "purpose": "To gauge the candidate's motivation",
                "good_answer_criteria": "Alignment with job responsibilities"
            })
        
        return script
    
    def generate_follow_up(self, question: str, response: str) -> Optional[str]:
        """Generate a follow-up question based on the candidate's response."""
        logger.info("Generating follow-up question")
        
        # Track follow-up history to avoid repetitive follow-ups
        if not hasattr(self, '_follow_up_count'):
            self._follow_up_count = {}
            
        # Get the count for this question or initialize to 0
        question_key = question[:50]  # Use prefix as key to avoid memory issues
        current_count = self._follow_up_count.get(question_key, 0)
        
        # Limit follow-ups per question to prevent getting stuck
        # Allow up to 2 follow-ups for more dynamic conversation
        if current_count >= 2:
            logger.info(f"Already asked multiple follow-ups for this question, moving on")
            return None
            
        # If response is too short, follow up but don't go overboard
        if len(response.split()) < 20:
            self._follow_up_count[question_key] = current_count + 1
            return "Could you please elaborate more on your answer? I'd like to hear more specific details about your experience."
        
        # Create enhanced prompt for follow-up generation with better context awareness 
        # and advanced conversation capabilities
        prompt = f"""
        You are an expert technical interviewer with excellent conversational skills. You need to decide if and how to follow up on a candidate's response.

        CONVERSATION CONTEXT:
        Original question: "{question}"
        Candidate's response: "{response}"

        ANALYSIS INSTRUCTIONS:
        1. Evaluate the response quality on these dimensions:
           - Completeness: Does it fully address all aspects of the question?
           - Specificity: Does it include concrete examples, metrics, or details that demonstrate actual experience?
           - Technical depth: Does it show appropriate technical understanding for the role?
           - Relevance: Does it directly address the core intent of the question?
           - Communication: Is it clear, structured, and professionally articulated?
        
        2. Identify what's missing or could be expanded upon:
           - What specific examples could strengthen their response?
           - What technical details would you like them to elaborate on?
           - What aspects of the question did they overlook or not fully address?
           - What follow-up would reveal more about their capabilities or experience?

        RESPONSE INSTRUCTIONS:
        If the response is truly comprehensive and no valuable follow-up is needed, respond with EXACTLY: "NO_FOLLOW_UP_NEEDED"
        
        Otherwise, craft ONE follow-up question that:
        - Targets the most important gap or opportunity in their response
        - Uses natural, conversational language (like a real interviewer would)
        - Encourages specific examples or technical details
        - Shows active listening by referencing something they said
        - Is open-ended (not yes/no)
        - Feels like a natural progression of the conversation

        Your entire response must be ONLY the follow-up question text with no additional commentary.
        Make the question direct, concise, and specific.
        """
        
        try:
            follow_up = self.llm.generate_text(prompt)
            
            # Strictly clean the response
            cleaned_follow_up = self._extract_question_only(follow_up)
            
            # Check for explicit rejection
            if "NO_FOLLOW_UP_NEEDED" in follow_up:
                logger.info("No follow-up needed (explicit rejection)")
                return None
                
            # Check if the response indicates no follow-up is needed
            if cleaned_follow_up.strip().lower() in ["none", "no follow-up needed", "no follow-up necessary", ""]:
                logger.info("No follow-up needed")
                return None
            
            # Increment the follow-up count for this question
            self._follow_up_count[question_key] = current_count + 1
            
            logger.info("Generated follow-up question")
            return cleaned_follow_up.strip()
        except Exception as e:
            logger.error(f"Error generating follow-up question: {str(e)}")
            return None
            
    def _extract_question_only(self, text: str) -> str:
        """Extract just the question from a potentially verbose LLM response."""
        import re
        
        # Remove any explanatory phrases that might precede the question
        text = re.sub(r'(?i)(follow-up question:|i would ask:|here\'s a follow-up:|my follow-up would be:|follow up:|answer:)', '', text)
        
        # Check for a question mark - the most reliable indicator of a question
        question_sentences = re.findall(r'[^.!?]*\?', text)
        if question_sentences:
            # Return the first question found
            return question_sentences[0].strip()
            
        # Try splitting by newlines and take the last non-empty line that isn't a standard rejection
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        filtered_lines = [line for line in lines if line.lower() not in ["none", "no follow-up needed", "no follow-up necessary"]]
        
        if filtered_lines:
            # Get the last non-rejection line
            return filtered_lines[-1].strip()
            
        # If all else fails, return a cleaned version of the original text
        cleaned = re.sub(r'\s+', ' ', text).strip()
        
        # If it's a very long response, it's likely reasoning rather than a question
        if len(cleaned) > 150:
            return ""
            
        return cleaned
    
    def generate_interview_summary(
            self, 
            job_data: Dict[str, Any], 
            company_data: Dict[str, Any],
            candidate_data: Dict[str, Any],
            responses: List[Dict[str, Any]],
            early_termination: bool = False
        ) -> Dict[str, Any]:
        """Generate a summary of the interview based on the candidate's responses."""
        logger.info("Generating interview summary")
        
        # Log inputs for debugging
        logger.debug(f"Summary generation inputs: {len(responses)} responses, early_termination={early_termination}")
        
        try:
            # Prepare a prompt for the LLM to generate a structured summary
            prompt = self._create_summary_prompt(job_data, company_data, candidate_data, responses, early_termination)
            
            # Generate the summary using the LLM
            response = self.llm.generate_text(prompt)
            
            # Parse the response
            summary = self._parse_summary_response(response, candidate_data, job_data)
            
            logger.info("Successfully generated interview summary")
            logger.debug(f"Summary generation result keys: {list(summary.keys())}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating interview summary: {str(e)}")
            logger.exception("Exception details:")
            
            # Create a basic summary with candidate info
            basic_summary = {
                "candidate_name": candidate_data.get("name", "Candidate"),
                "position": job_data.get("title", "Position"),
                "strengths": ["Could not generate complete summary"],
                "areas_for_improvement": ["Could not generate complete summary"],
                "technical_evaluation": "Error generating summary",
                "cultural_fit": "Error generating summary",
                "recommendation": "Unable to provide recommendation due to error",
                "next_steps": "Review interview transcript manually",
                "overall_assessment": f"An error occurred while generating the summary: {str(e)}"
            }
            
            return basic_summary
    
    def _create_summary_prompt(self, job_data: Dict[str, Any], 
                                company_data: Dict[str, Any], 
                                candidate_data: Dict[str, Any],
                                responses: List[Dict[str, Any]],
                                early_termination: bool = False) -> str:
        """Create a prompt for generating the interview summary."""
        
        job_title = job_data.get('title', 'the position')
        company_name = company_data.get('name', 'the company')
        candidate_name = candidate_data.get('name', 'the candidate')
        required_skills = job_data.get('required_skills', 'Not provided')
        
        # Handle required_skills whether it's a string or list
        if isinstance(required_skills, str):
            if required_skills == "Not provided":
                skills_list = ""
            else:
                skills = [skill.strip() for skill in required_skills.split(',')]
                skills_list = ", ".join([f"'{skill}'" for skill in skills])
        elif isinstance(required_skills, list):
            skills_list = ", ".join([f"'{skill}'" for skill in required_skills])
        else:
            skills_list = ""
        
        # Create an enhanced prompt for summary generation
        prompt = f"""
        You are an experienced hiring manager for {company_name} with 15+ years of technical interviewing expertise. 
        You have just completed an interview with {candidate_name} for the {job_title} position.
        
        Job Requirements:
        {job_data.get('description', 'Not provided')}
        
        Required Skills: {required_skills if isinstance(required_skills, str) else ", ".join(required_skills)}
        
        Company Values:
        {company_data.get('values', 'Not provided')}
        
        Interview Questions and Responses:
        """
        
        # Add questions and responses to the prompt, with flags for duplicates
        for response in responses:
            q_index = response.get('question_index', 0)
            q_text = response.get('question', 'Unknown question')
            r_text = response.get('response', 'No response provided')
            category = response.get('category', 'general')
            is_duplicate = response.get('is_duplicate', False)
            
            prompt += f"\nCategory: {category}\n"
            prompt += f"Question {q_index + 1}: {q_text}\n"
            prompt += f"Response: {r_text}\n"
            
            if is_duplicate:
                prompt += f"Note: This response was very similar to a previous answer.\n"
        
        prompt += f"""
        Based on the above interview, provide a comprehensive and specific evaluation including:

        1. Key strengths (3-5) demonstrated by the candidate - be specific with exact examples from their responses
           For each strength, include a direct quote or paraphrase from their responses as evidence
        
        2. Areas for improvement or exploration (2-4) - identify specific gaps or weaknesses
           For each area, suggest specific development opportunities or follow-up questions
        
        3. Technical skill assessment - evaluate the candidate against each of these required skills: {skills_list}
           Rate their proficiency in each skill (Not Demonstrated, Basic, Proficient, Expert)
        
        4. Cultural fit assessment - analyze how well they align with these company values: {company_data.get('values', 'Not provided')}
           For each value, note specific evidence from their responses
        
        5. Clear hiring recommendation with detailed justification:
           - Highly Recommend (Clear evidence of exceptional fit)
           - Recommend (Strong match with minor reservations)
           - Neutral (Equal strengths and concerns)
           - Do Not Recommend (Significant gaps or concerns)
        
        6. Concrete next steps - specific, actionable items for the hiring process:
           - Suggested follow-up questions for a second interview
           - Recommended technical assessments
           - Potential team members to meet
        
        7. Overall assessment (2-3 paragraphs) - a balanced evaluation highlighting:
           - Evidence-based analysis of fit for the role
           - Specific quotes or examples from their responses
           - How their background aligns with the position
           - Potential growth trajectory within the company
        
        Format the response as JSON with this structure:
        ```json
        {{
            "candidate_name": "{candidate_name}",
            "position": "{job_title}",
            "strengths": [
                "Strength 1 with evidence: ...",
                "Strength 2 with evidence: ...",
                "..."
            ],
            "areas_for_improvement": [
                "Area 1 with specific development suggestion: ...",
                "Area 2 with specific development suggestion: ...",
                "..."
            ],
            "technical_evaluation": "Detailed assessment of technical skills with evidence from the interview...",
            "cultural_fit": "Specific evaluation of alignment with company values with examples...",
            "recommendation": "Clear recommendation with thorough justification...",
            "next_steps": "Specific, actionable next steps for the hiring process...",
            "overall_assessment": "Balanced, evidence-based evaluation with specific examples..."
        }}
        ```
        
        IMPORTANT GUIDELINES:
        - Be specific and evidence-based, directly referencing candidate responses
        - Avoid generic statements that could apply to any candidate
        - Focus on quality over quantity in your assessment
        - Be fair and balanced, acknowledging both strengths and weaknesses
        - Keep evaluations professional and constructive
        - Use direct quotes or paraphrases from the candidate whenever possible
        """
        
        return prompt
    
    def _parse_summary_response(self, response: str, candidate_data: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the LLM response into a structured interview summary."""
        try:
            # Extract JSON from response (if response contains markdown code blocks)
            import json
            import re
            
            # Try to extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if json_match:
                json_str = json_match.group(1)
            else:
                # If no code blocks, try to parse the whole response
                json_str = response
            
            # Parse the JSON
            summary = json.loads(json_str)
            
            # Validate required fields
            required_fields = [
                'strengths', 'areas_for_improvement', 'technical_evaluation',
                'cultural_fit', 'recommendation', 'next_steps', 'overall_assessment'
            ]
            
            for field in required_fields:
                if field not in summary:
                    logger.warning(f"Missing required field '{field}' in summary")
                    if field in ['strengths', 'areas_for_improvement']:
                        summary[field] = []
                    else:
                        summary[field] = "Not provided"
            
            # Fix next_steps if it's an array or object instead of a string
            if 'next_steps' in summary:
                if isinstance(summary['next_steps'], list):
                    # Join the list into a comma-separated string
                    summary['next_steps'] = ", ".join(summary['next_steps'])
                elif isinstance(summary['next_steps'], dict):
                    # Convert the object to a formatted string
                    steps_str = []
                    for key, value in summary['next_steps'].items():
                        steps_str.append(f"{key}: {value}")
                    summary['next_steps'] = "; ".join(steps_str)
            
            # Ensure candidate info is present
            summary['candidate_name'] = summary.get('candidate_name', candidate_data.get('name', 'Candidate'))
            summary['position'] = summary.get('position', job_data.get('title', 'Position'))
            
            return summary
            
        except Exception as e:
            logger.error(f"Error parsing summary response: {str(e)}")
            raise ValueError(f"Failed to parse interview summary: {str(e)}")

    def _initialize_llm_adapter(self, ollama_api_base=None, ollama_api_key=None):
        """Initialize the LLM adapter with the appropriate configurations."""
        logger.info("Initializing LLM adapter")
        
        if ollama_api_base is not None:
            os.environ["OLLAMA_API_BASE"] = ollama_api_base
        
        if ollama_api_key is not None:
            os.environ["OLLAMA_API_KEY"] = ollama_api_key
        
        self.llm_adapter = get_llm_adapter()
        logger.info(f"Using LLM adapter: {type(self.llm_adapter).__name__}")

    def generate_follow_up_question(self, current_question, response_text, job_data=None, company_data=None, candidate_data=None):
        """Generate a follow-up question with Llama3-optimized prompting"""
        logger.info("Generating follow-up question")
        
        # Create a carefully structured prompt for Llama3
        prompt = f"""<|system|>
You are an expert technical interviewer working for a leading technology company. You need to decide if a candidate's response requires a follow-up question.
</|system|>

<|user|>
I asked this interview question: "{current_question.get('question', '')}"

The candidate responded: "{response_text}"

For context, this is for a {job_data.get('title', 'position')} role.

Questions to consider:
1. Did the candidate fully answer the question?
2. Did they provide specific examples/details?
3. Is there a skill area that needs deeper probing?

If NO follow-up is needed, respond with exactly: "NO_FOLLOW_UP_NEEDED"

If a follow-up IS needed, respond with ONE brief, focused follow-up question (under 15 words) that references something specific from their response.
</|user|>
"""

        # Add timeout handling for demo reliability
        try:
            # Set a timer to ensure response within 5 seconds for demo
            import threading
            import queue
            
            result_queue = queue.Queue()
            
            def generate_with_timeout():
                try:
                    result = self._generate_with_llm(prompt, max_tokens=100)
                    result_queue.put(result)
                except Exception as e:
                    logger.error(f"Error in follow-up generation: {e}")
                    result_queue.put(None)
            
            thread = threading.Thread(target=generate_with_timeout)
            thread.daemon = True
            thread.start()
            
            # Wait for result with timeout appropriate for demo
            try:
                follow_up = result_queue.get(timeout=5)
                if follow_up is None or "NO_FOLLOW_UP_NEEDED" in follow_up:
                    return None
                    
                # Clean up the response - extract just the question
                import re
                question_match = re.search(r'([^.!?]*\?)', follow_up)
                if question_match:
                    return question_match.group(1).strip()
                
                # Remove any extra text
                follow_up = re.sub(r'(^|\n).*?(follow-up|followup).*?:', '', follow_up, flags=re.IGNORECASE)
                
                return follow_up.strip()
            except queue.Empty:
                logger.warning("Follow-up generation timed out")
                return "Could you elaborate more on that point?"
                
        except Exception as e:
            logger.error(f"Error generating follow-up: {e}")
            return "Could you share a specific example of that?"

    def generate_transition(self, contextual_prompt, current_response, current_question, next_question):
        """Generate a natural transition between questions based on conversation memory."""
        logger.info("Generating natural transition between questions")
        
        prompt = contextual_prompt
        
        try:
            transition = self._generate_with_llm(prompt, max_tokens=150)
            
            # Clean up the response
            transition = transition.strip()
            if transition.startswith('"') and transition.endswith('"'):
                transition = transition[1:-1].strip()
            
            return transition
        except Exception as e:
            logger.error(f"Error generating transition: {e}")
            return next_question.get("transition", "Let's move on to the next question.")

    def _generate_with_llm(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.7) -> str:
        """Helper method to generate text using the LLM interface."""
        try:
            return self.llm.generate_text(prompt, max_tokens=max_tokens, temperature=temperature)
        except Exception as e:
            logger.error(f"Error generating text with LLM: {e}")
            raise 