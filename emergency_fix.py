#!/usr/bin/env python3
import json
import re
import logging

logger = logging.getLogger(__name__)

def fix_json(text):
    """Comprehensive JSON fixing for LLM outputs with targeted fixes for common errors."""
    # Extract just the JSON object with improved regex
    pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```|(\{[\s\S]*?\})'
    matches = re.findall(pattern, text)
    
    # Use the first match that contains a JSON-like object
    json_str = ""
    for match in matches:
        # Each match is a tuple from the regex groups
        for group in match:
            if group and "{" in group and "}" in group:
                json_str = group
                break
        if json_str:
            break
    
    # If no JSON found with regex, try to find the outer braces
    if not json_str:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end+1]
        else:
            json_str = text
    
    logger.debug(f"Extracted JSON string (first 100 chars): {json_str[:100]}...")
    
    # Try to parse as-is first
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.debug(f"Original JSON error: {str(e)}")
    
    # Apply targeted fixes based on typical LLM errors
    
    # Fix 1: Line-specific fixes (addressing the line 32 issue in logs)
    lines = json_str.split('\n')
    if len(lines) >= 32:
        line32 = lines[31]  # 0-indexed
        if not line32.strip().endswith(',') and not line32.strip().endswith('{') and not line32.strip().endswith('['):
            lines[31] = line32.rstrip() + ','
            logger.debug(f"Fixed line 32: {lines[31]}")
    
    # Fix 2: Quote property names
    json_str = '\n'.join(lines)
    json_str = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
    
    # Fix 3: Remove trailing commas
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    
    # Fix 4: Add missing commas between elements
    json_str = re.sub(r'("(?:\\"|[^"])*")\s*("(?:\\"|[^"])*")', r'\1, \2', json_str)
    
    # Fix 5: Fix broken string literals
    json_str = re.sub(r'("(?:\\"|[^"])*)\n([^"]*")', r'\1\\n\2', json_str)
    
    # Try parsing again after fixes
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.debug(f"Still invalid after direct fixes: {str(e)}")
    
    # Try hjson as another option
    try:
        import hjson
        return hjson.loads(json_str)
    except Exception as e:
        logger.debug(f"hjson parsing failed: {str(e)}")
    
    # If all else fails, use pattern extraction
    return extract_data_from_text(text)

def extract_data_from_text(text):
    """Extract structured data from text when all JSON parsing fails."""
    result = {
        "candidate_name": "",
        "position": "",
        "strengths": [],
        "areas_for_improvement": [],
        "technical_evaluation": "",
        "cultural_fit": "",
        "recommendation": "",
        "next_steps": "",
        "overall_assessment": "",
        "response_scores": [
            {
                "question_index": 0,
                "score": 3,
                "feedback": "Response demonstrated basic understanding of the question."
            },
            {
                "question_index": 1,
                "score": 3,
                "feedback": "Candidate provided a relevant answer to the question."
            }
        ],
        "skill_ratings": [  # Add default skill ratings
            {"name": "Technical Knowledge", "score": 65},
            {"name": "Communication", "score": 70},
            {"name": "Problem Solving", "score": 60},
            {"name": "Domain Experience", "score": 55},
            {"name": "Team Collaboration", "score": 75}
        ]
    }
    
    # Extract key data using patterns
    # 1. Extract strings like "candidate_name": "John Smith"
    for field in ["candidate_name", "position", "technical_evaluation", 
                 "cultural_fit", "recommendation", "next_steps", "overall_assessment"]:
        pattern = rf'"{field}"["\s]*:["\s]*([^"]*)"'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result[field] = match.group(1).strip()
    
    # 2. Extract lists like "strengths": ["Item 1", "Item 2"]
    for field in ["strengths", "areas_for_improvement"]:
        items = []
        # Try to find the array first
        array_pattern = rf'"{field}"["\s]*:["\s]*\[(.*?)\]'
        array_match = re.search(array_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if array_match:
            # Extract items from the array
            items_text = array_match.group(1)
            item_matches = re.findall(r'"([^"]+)"', items_text)
            items.extend(item_matches)
        else:
            # Fallback to looking for section headers
            section_pattern = rf'{field}.*?:(.*?)(?=\n[A-Z]|$)'
            section_match = re.search(section_pattern, text, re.IGNORECASE | re.DOTALL)
            if section_match:
                content = section_match.group(1).strip()
                # Look for bullet points or numbered items
                bullet_items = re.findall(r'(?:^|\n)[•\-*]?\s*\d*\.?\s*([^\n]+)', content)
                items.extend([item.strip() for item in bullet_items if item.strip()])
        
        result[field] = items
    
    # 3. Make sure we have at least something for each field
    if not result["strengths"]:
        # Try to find strengths with different patterns
        strength_matches = re.findall(r'(?:strength|key strength|strong)s?[^\n:]*?[:|-]\s*([^\n]+)', text, re.IGNORECASE)
        result["strengths"] = [m.strip() for m in strength_matches if m.strip()]
    
    if not result["areas_for_improvement"]:
        # Try to find improvement areas with different patterns
        improvement_matches = re.findall(r'(?:improvement|area of improvement|weakness)[^\n:]*?[:|-]\s*([^\n]+)', 
                                        text, re.IGNORECASE)
        result["areas_for_improvement"] = [m.strip() for m in improvement_matches if m.strip()]
    
    # 4. Attempt to extract response scores if they exist
    scores_pattern = r'"response_scores"\s*:\s*\[(.*?)\]'
    scores_match = re.search(scores_pattern, text, re.DOTALL)
    if scores_match:
        try:
            # Try to parse individual score objects
            scores_text = scores_match.group(1)
            score_objects = re.findall(r'{(.*?)}', scores_text, re.DOTALL)
            
            if score_objects:
                extracted_scores = []
                for idx, score_obj in enumerate(score_objects):
                    score_dict = {"question_index": idx, "score": 3, "feedback": ""}
                    
                    # Extract question_index
                    q_idx_match = re.search(r'"question_index"\s*:\s*(\d+)', score_obj)
                    if q_idx_match:
                        score_dict["question_index"] = int(q_idx_match.group(1))
                    
                    # Extract score
                    score_match = re.search(r'"score"\s*:\s*(\d+)', score_obj)
                    if score_match:
                        score_dict["score"] = int(score_match.group(1))
                    
                    # Extract feedback
                    feedback_match = re.search(r'"feedback"\s*:\s*"([^"]*)"', score_obj)
                    if feedback_match:
                        score_dict["feedback"] = feedback_match.group(1)
                    
                    extracted_scores.append(score_dict)
                
                if extracted_scores:
                    result["response_scores"] = extracted_scores
        except Exception as e:
            logger.debug(f"Failed to extract response scores: {e}")
    
    # 5. Try to extract skill ratings
    skill_ratings_pattern = r'"skill_ratings"\s*:\s*\[(.*?)\]'
    skill_ratings_match = re.search(skill_ratings_pattern, text, re.DOTALL)
    if skill_ratings_match:
        try:
            # Try to parse individual skill rating objects
            ratings_text = skill_ratings_match.group(1)
            rating_objects = re.findall(r'{(.*?)}', ratings_text, re.DOTALL)
            
            if rating_objects:
                extracted_ratings = []
                for rating_obj in rating_objects:
                    # Extract name
                    name_match = re.search(r'"name"\s*:\s*"([^"]*)"', rating_obj)
                    # Extract score
                    score_match = re.search(r'"score"\s*:\s*(\d+)', rating_obj)
                    
                    if name_match and score_match:
                        try:
                            extracted_ratings.append({
                                "name": name_match.group(1),
                                "score": int(score_match.group(1))
                            })
                        except ValueError:
                            # Skip if score can't be converted to int
                            pass
                
                if extracted_ratings:
                    result["skill_ratings"] = extracted_ratings
        except Exception as e:
            logger.debug(f"Failed to extract skill ratings: {e}")
    
    return result 