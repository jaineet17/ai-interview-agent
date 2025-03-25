from typing import Dict, Any, List, Optional
import logging
import os
import json

logger = logging.getLogger(__name__)

class LLMInterface:
    """Provides a standardized interface for LLM interactions."""
    
    def __init__(self, provider: str = "openai", model_name: Optional[str] = None):
        """Initialize the LLM interface with a provider and model.
        
        Args:
            provider: The LLM provider to use ('openai', 'anthropic', etc.)
            model_name: The specific model to use (e.g., 'gpt-4', 'claude-3-opus')
                        If None, a default will be selected based on the provider.
        """
        self.provider = provider.lower()
        self.model_name = model_name
        self._client = None
        
        # Initialize the appropriate client
        self._setup_client()
        logger.info(f"Initialized LLM interface with provider: {provider}")
    
    def _setup_client(self):
        """Set up the client for the specified provider."""
        try:
            if self.provider == "openai":
                self._setup_openai()
            elif self.provider == "anthropic":
                self._setup_anthropic()
            else:
                logger.error(f"Unsupported LLM provider: {self.provider}")
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        except Exception as e:
            logger.error(f"Error setting up LLM client: {str(e)}")
            raise
    
    def _setup_openai(self):
        """Set up the OpenAI client."""
        try:
            from openai import OpenAI
            
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                logger.error("OPENAI_API_KEY not found in environment variables")
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            
            self._client = OpenAI(api_key=api_key)
            
            # Set default model if not specified
            if not self.model_name:
                self.model_name = "gpt-4"
                logger.info(f"Using default OpenAI model: {self.model_name}")
        except ImportError:
            logger.error("OpenAI package not installed. Install with 'pip install openai'")
            raise
    
    def _setup_anthropic(self):
        """Set up the Anthropic client."""
        try:
            from anthropic import Anthropic
            
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                logger.error("ANTHROPIC_API_KEY not found in environment variables")
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            
            self._client = Anthropic(api_key=api_key)
            
            # Set default model if not specified
            if not self.model_name:
                self.model_name = "claude-3-opus-20240229"
                logger.info(f"Using default Anthropic model: {self.model_name}")
        except ImportError:
            logger.error("Anthropic package not installed. Install with 'pip install anthropic'")
            raise
    
    def generate_text(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.7) -> str:
        """Generate text using the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0.0-1.0)
        
        Returns:
            str: The generated text
        """
        if not self._client:
            logger.error("LLM client not initialized")
            raise ValueError("LLM client not initialized")
        
        try:
            if self.provider == "openai":
                return self._generate_openai(prompt, max_tokens, temperature)
            elif self.provider == "anthropic":
                return self._generate_anthropic(prompt, max_tokens, temperature)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise
    
    def _generate_openai(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate text using OpenAI's API."""
        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract and return the generated text
            generated_text = response.choices[0].message.content
            logger.debug(f"Generated {len(generated_text)} chars of text with OpenAI")
            return generated_text
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def _generate_anthropic(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate text using Anthropic's API."""
        try:
            response = self._client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract and return the generated text
            generated_text = response.content[0].text
            logger.debug(f"Generated {len(generated_text)} chars of text with Anthropic")
            return generated_text
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise
    
    def analyze_json(self, prompt: str, json_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured JSON responses based on a prompt and expected structure.
        
        Args:
            prompt: The prompt to send to the LLM
            json_structure: A template of the expected JSON structure
        
        Returns:
            Dict: The generated JSON response
        """
        # Create a prompt that instructs the model to return a valid JSON
        json_prompt = f"""
        {prompt}
        
        Respond ONLY with a valid JSON object that matches this structure:
        {json.dumps(json_structure, indent=2)}
        
        Your response must be a valid JSON object.
        """
        
        try:
            response_text = self.generate_text(json_prompt, temperature=0.3)
            
            # Extract JSON from the response
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
            
            if json_match:
                json_str = json_match.group(1)
            else:
                # If no code blocks, try to parse the whole response
                json_str = response_text
            
            # Parse the JSON
            result = json.loads(json_str)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {str(e)}")
            logger.debug(f"Raw response: {response_text}")
            raise ValueError(f"Failed to parse JSON from LLM response: {str(e)}")
        except Exception as e:
            logger.error(f"Error in analyze_json: {str(e)}")
            raise 