import logging
import os
import re
import time
from typing import Dict, Any, Optional, List

from llm_service import LLMService, OllamaProvider, LLMProvider

logger = logging.getLogger(__name__)

class LLMAdapter:
    """Adapter for LLM providers to standardize interfaces."""
    
    def __init__(self, provider: str = None, model_name: Optional[str] = None):
        """Initialize the LLM adapter."""
        # Get the provider from environment or default to OpenAI
        self.provider_name = provider or os.getenv("LLM_PROVIDER", "ollama")
        
        # Initialize the appropriate provider
        self.model_name = model_name
        if not self.model_name:
            if self.provider_name.lower() == "ollama":
                self.model_name = os.getenv("OLLAMA_MODEL", "llama3")
            elif self.provider_name.lower() == "openai":
                self.model_name = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            elif self.provider_name.lower() == "anthropic":
                self.model_name = os.getenv("ANTHROPIC_MODEL", "claude-2")
        
        # Get the appropriate provider from LLMService
        self.llm_provider = LLMService.get_provider(provider_name=self.provider_name, model=self.model_name)
        
        logger.info(f"LLM adapter initialized with provider: {self.provider_name}, model: {self.model_name}")
        
        # Pre-warm the model if using Ollama for better demo experience
        if self.provider_name.lower() == "ollama":
            self._pre_warm_model()
    
    def _pre_warm_model(self):
        """Pre-warm the Ollama model to ensure fast responses during demo"""
        try:
            logger.info(f"Pre-warming {self.model_name} model...")
            # Simple warm-up prompt
            self.llm_provider.get_completion(
                "Analyze this sentence structure carefully.",
                max_tokens=10
            )
            logger.info("Model pre-warming complete")
        except Exception as e:
            logger.warning(f"Model pre-warming failed: {e}")
    
    def generate_text(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.7) -> str:
        """Generate text from the LLM."""
        start_time = time.time()
        logger.debug(f"Generating text with {self.provider_name}, prompt length: {len(prompt)}")
        
        try:
            response = self.llm_provider.get_completion(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            end_time = time.time()
            duration = end_time - start_time
            logger.debug(f"Text generation completed in {duration:.2f}s, response length: {len(response)}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise
    
    def classify_text(self, text: str, categories: List[str], prompt_template: Optional[str] = None) -> str:
        """Classify text into one of the provided categories."""
        logger.debug(f"Classifying text into {len(categories)} categories")
        
        # Default prompt template if none provided
        if not prompt_template:
            prompt_template = """
            Classify the following text into one of these categories: {categories}
            
            Text to classify: "{text}"
            
            Response format: Return ONLY the category name, with no additional text, quotes, or explanation.
            """
        
        # Format the prompt
        prompt = prompt_template.format(
            categories=", ".join(categories),
            text=text
        )
        
        try:
            response = self.generate_text(prompt, max_tokens=100, temperature=0.3)
            
            # Clean up the response
            response = response.strip().strip('"\'')
            
            # Check if the response is one of the categories
            for category in categories:
                if category.lower() in response.lower():
                    return category
            
            # If no match, return the raw response
            return response
            
        except Exception as e:
            logger.error(f"Error classifying text: {str(e)}")
            return categories[0]  # Default to first category on error
    
    def extract_structured_data(self, text: str, schema: Dict[str, Any], prompt_template: Optional[str] = None) -> Dict[str, Any]:
        """Extract structured data from text based on the provided schema."""
        logger.debug(f"Extracting structured data with schema: {schema.keys()}")
        
        # Default prompt template if none provided
        if not prompt_template:
            prompt_template = """
            Extract the following information from the text below according to this schema:
            {schema_description}
            
            Text: "{text}"
            
            Response format: Return a valid JSON object with ONLY the extracted fields.
            """
        
        # Create a description of the schema
        schema_description = "\n".join([f"- {key}: {value}" for key, value in schema.items()])
        
        # Format the prompt
        prompt = prompt_template.format(
            schema_description=schema_description,
            text=text
        )
        
        try:
            response = self.generate_text(prompt, max_tokens=2000, temperature=0.2)
            
            # Try to extract JSON from the response
            import json
            
            # Look for JSON in code blocks
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Otherwise use the whole response
                json_str = response
            
            # Clean up the JSON string
            json_str = self._fix_json_string(json_str)
            
            # Parse the JSON
            data = json.loads(json_str)
            
            # Validate the data against the schema
            for key in schema:
                if key not in data:
                    data[key] = None
            
            return data
            
        except Exception as e:
            logger.error(f"Error extracting structured data: {str(e)}")
            # Return an empty object with the schema keys
            return {key: None for key in schema}
    
    def _fix_json_string(self, json_str: str) -> str:
        """Fix common issues with JSON strings."""
        import re
        
        # Replace single quotes with double quotes
        json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
        
        # Fix unquoted property names
        json_str = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
        
        # Fix trailing commas
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        return json_str
    
    def get_completion(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.7) -> str:
        """Alias for generate_text to maintain compatibility with interview_generator's expectations."""
        return self.generate_text(prompt, max_tokens, temperature)

def get_llm_adapter(provider: str = None, model_name: Optional[str] = None) -> 'LLMAdapter':
    """Get an instance of the LLMAdapter.
    
    Args:
        provider: The LLM provider name (e.g., 'ollama', 'openai', 'anthropic')
        model_name: The model name to use
    
    Returns:
        LLMAdapter: An instance of the LLM adapter
    """
    return LLMAdapter(provider=provider, model_name=model_name) 