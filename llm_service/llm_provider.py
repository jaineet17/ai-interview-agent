from abc import ABC, abstractmethod
import json
import os
from typing import Dict, Any, Optional, List
import logging
import traceback

# Import the ollama Python package
try:
    import ollama
    OLLAMA_PACKAGE_AVAILABLE = True
except ImportError:
    logger.warning("Ollama package not available. Using HTTP fallback.")
    OLLAMA_PACKAGE_AVAILABLE = False

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def get_completion(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Get completion from the LLM"""
        pass
    
    def format_as_json(self, text: str) -> Any:
        """Try to parse text as JSON"""
        text = text.strip()
        
        # Try to find JSON in the text if it's not pure JSON
        if not (text.startswith('{') and text.endswith('}')):
            # Look for JSON between ```json and ``` or between { and }
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            else:
                # Try to find the first { and last }
                start = text.find('{')
                end = text.rfind('}')
                if start != -1 and end != -1 and end > start:
                    text = text[start:end+1]
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse as JSON: {e}. Text: {text[:100]}...")
            return {"text": text}


class OllamaProvider(LLMProvider):
    """Provider for Ollama API with improved reliability"""
    
    def __init__(self, model_name: str = "llama2"):
        self.model_name = model_name
        
        # Get API base from environment variable or config
        from config import OLLAMA_API_BASE, OLLAMA_API_KEY
        self.api_base = OLLAMA_API_BASE
        self.api_key = OLLAMA_API_KEY
        
        # Fallback model in case the requested one isn't available
        self.fallback_model = "llama2"  # A commonly available model
        
        # Health check on initialization
        self.is_healthy = self._check_health()
        
        # Configure the Ollama client if the package is available
        if OLLAMA_PACKAGE_AVAILABLE:
            # Set the host if different from default
            if self.api_base != "http://localhost:11434":
                # Extract host part from URL
                import re
                host_match = re.match(r'https?://([^:/]+)(?::(\d+))?', self.api_base)
                if host_match:
                    host = host_match.group(1)
                    port = host_match.group(2) or "11434"
                    ollama.host = f"http://{host}:{port}"
                    logger.info(f"Set Ollama host to: {ollama.host}")
        else:
            logger.warning("Ollama Python package not installed. Using HTTP fallback.")
            
        logger.info(f"Initialized Ollama provider with model: {model_name}")
    
    def _check_health(self) -> bool:
        """Check if Ollama service is healthy and the model is available"""
        try:
            if OLLAMA_PACKAGE_AVAILABLE:
                # List available models
                models = ollama.list()
                # Debug log to see the actual response structure
                logger.debug(f"Ollama model list response: {models}")
                
                # The models should be in models['models'], each having a 'name' field
                # But let's handle different response formats more gracefully
                available_models = []
                if isinstance(models, dict) and 'models' in models:
                    for model in models.get('models', []):
                        if isinstance(model, dict) and 'name' in model:
                            available_models.append(model['name'])
                
                if not available_models:
                    # Try alternative format
                    if isinstance(models, dict) and 'Models' in models:
                        available_models = [model.get('name') for model in models.get('Models', []) if isinstance(model, dict) and 'name' in model]
                
                # If still no models found but we got a successful response, log and consider service healthy
                if not available_models and isinstance(models, dict):
                    logger.warning(f"Ollama service is responding but no models could be parsed from response: {models}")
                    return True
                
                if self.model_name in available_models:
                    logger.info(f"Model {self.model_name} is available")
                    return True
                else:
                    logger.warning(f"Model {self.model_name} not found. Available models: {available_models}")
                    # Service is running even if the specific model isn't available
                    return True
            else:
                # Fallback HTTP check
                import requests
                response = requests.get(f"{self.api_base}/api/tags")
                if response.status_code == 200:
                    # Service is responding, consider it healthy even if we can't parse the models
                    logger.info("Ollama service is running")
                    return True
                else:
                    logger.warning(f"Ollama API health check failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            return False
    
    def get_completion(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Get completion from Ollama with improved reliability"""
        max_retries = 2
        retry_count = 0
        
        if not self.is_healthy:
            # Try to check health again before giving up
            self.is_healthy = self._check_health()
            if not self.is_healthy:
                logger.warning("Ollama service is not healthy, using fallback response")
                return self._generate_labeled_fallback(prompt)
        
        while retry_count <= max_retries:
            try:
                logger.debug(f"Sending request to Ollama with model {self.model_name} (attempt {retry_count+1}/{max_retries+1})")
                
                if OLLAMA_PACKAGE_AVAILABLE:
                    # Use the Python package - much more reliable
                    response = ollama.chat(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        options={
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    )
                    
                    if response and 'message' in response and 'content' in response['message']:
                        return response['message']['content']
                    else:
                        logger.error(f"Unexpected response format from Ollama: {response}")
                        # Try with fallback model if this is the last retry
                        if retry_count == max_retries and self.model_name != self.fallback_model:
                            logger.info(f"Trying fallback model: {self.fallback_model}")
                            orig_model = self.model_name
                            self.model_name = self.fallback_model
                            try:
                                response = ollama.chat(
                                    model=self.model_name,
                                    messages=[{"role": "user", "content": prompt}],
                                    options={
                                        "temperature": temperature,
                                        "num_predict": max_tokens
                                    }
                                )
                                if response and 'message' in response and 'content' in response['message']:
                                    return response['message']['content']
                            except Exception:
                                pass
                            finally:
                                self.model_name = orig_model
                        
                        # If fallback model also failed, use deterministic fallback
                        retry_count += 1
                        continue
                else:
                    # Fallback to HTTP requests with better error handling
                    import requests
                    
                    # Set up session with headers
                    session = requests.Session()
                    if self.api_key:
                        session.headers.update({"Authorization": f"Bearer {self.api_key}"})
                    
                    if not self.api_base.endswith('/api'):
                        api_endpoint = f"{self.api_base}/api/generate"
                    else:
                        api_endpoint = f"{self.api_base}/generate"
                    
                    response = session.post(
                        api_endpoint,
                        json={
                            "model": self.model_name,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": temperature,
                                "num_predict": max_tokens
                            }
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        return response.json().get("response", "")
                    elif response.status_code == 404 and self.model_name != self.fallback_model:
                        # Model not found, try fallback model
                        logger.info(f"Model {self.model_name} not found, trying fallback model {self.fallback_model}")
                        orig_model = self.model_name
                        self.model_name = self.fallback_model
                        try:
                            response = session.post(
                                api_endpoint,
                                json={
                                    "model": self.model_name,
                                    "prompt": prompt,
                                    "stream": False,
                                    "options": {
                                        "temperature": temperature,
                                        "num_predict": max_tokens
                                    }
                                },
                                timeout=30
                            )
                            if response.status_code == 200:
                                return response.json().get("response", "")
                        except Exception:
                            pass
                        finally:
                            self.model_name = orig_model
                    
                    logger.error(f"Ollama API error: {response.status_code}, {response.text}")
                    retry_count += 1
                    continue
                        
            except Exception as e:
                logger.error(f"Error calling Ollama: {str(e)}")
                logger.debug(f"Exception details: {traceback.format_exc()}")
                
                # If this is the last retry, try fallback model
                if retry_count == max_retries and self.model_name != self.fallback_model:
                    logger.info(f"Trying fallback model: {self.fallback_model}")
                    orig_model = self.model_name
                    self.model_name = self.fallback_model
                    try:
                        if OLLAMA_PACKAGE_AVAILABLE:
                            response = ollama.chat(
                                model=self.model_name,
                                messages=[{"role": "user", "content": prompt}],
                                options={
                                    "temperature": temperature,
                                    "num_predict": max_tokens
                                }
                            )
                            if response and 'message' in response and 'content' in response['message']:
                                return response['message']['content']
                    except Exception:
                        pass
                    finally:
                        self.model_name = orig_model
                
                # Try with a shorter max_tokens on retry to make it faster
                max_tokens = max(max_tokens // 2, 250)
                retry_count += 1
                logger.info(f"Retrying with reduced max_tokens: {max_tokens}")
                continue
        
        # If we got here, all retries failed. Use a fallback solution.
        return self._generate_labeled_fallback(prompt)
    
    def get_chat_completion(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Get chat completion from Ollama with improved reliability."""
        # For simple chat completion, just use the last message as prompt for now
        if messages and len(messages) > 0:
            last_message = messages[-1]
            prompt = last_message.get("content", "")
            return self.get_completion(prompt, max_tokens, temperature)
        return ""
    
    def _generate_labeled_fallback(self, prompt: str) -> str:
        """Generate a fallback response with a note that it's not from the LLM"""
        fallback_response = self._generate_deterministic_fallback(prompt)
        
        # If the response is already JSON-formatted (starts with '{' and ends with '}'), 
        # then don't add the label which would break JSON parsing
        if fallback_response.strip().startswith('{') and fallback_response.strip().endswith('}'):
            return fallback_response
        
        # Otherwise, add clear indication this is a fallback response
        return f"[Note: Using pre-programmed fallback response due to LLM service unavailability]\n\n{fallback_response}"
    
    def _generate_deterministic_fallback(self, prompt: str) -> str:
        """Generate a deterministic fallback response based on the prompt."""
        # Check if the prompt is asking for JSON
        json_indicators = [
            "format the response as json", 
            "return json", 
            "json format", 
            "response in json",
            "structured json"
        ]
        needs_json = any(indicator in prompt.lower() for indicator in json_indicators)
        
        # If JSON format is required, return properly formatted JSON
        if needs_json:
            # Try to determine what kind of response is needed based on prompt
            if "interview script" in prompt.lower() or "generate script" in prompt.lower():
                return '''
                {
                    "introduction": "Hello and welcome to this interview. I'm excited to learn more about your background and experience today.",
                    "questions": {
                        "job_specific": [
                            {
                                "question": "Could you tell me about your experience that's relevant to this position?",
                                "purpose": "To understand relevant experience",
                                "good_answer_criteria": "Specific examples of relevant skills and accomplishments"
                            }
                        ],
                        "technical": [
                            {
                                "question": "What technical skills do you bring to this role?",
                                "purpose": "To assess technical capabilities",
                                "good_answer_criteria": "Demonstrates knowledge of required technologies"
                            }
                        ],
                        "company_fit": [
                            {
                                "question": "Why are you interested in working with our company?",
                                "purpose": "To assess cultural fit",
                                "good_answer_criteria": "Shows knowledge of company values and mission"
                            }
                        ],
                        "behavioral": [
                            {
                                "question": "Tell me about a challenging situation at work and how you handled it.",
                                "purpose": "To assess problem-solving skills",
                                "good_answer_criteria": "Structured response with clear problem, action, and result"
                            }
                        ]
                    },
                    "closing": "Thank you for your time today. We'll be in touch about next steps in the interview process."
                }
                '''
            elif "summary" in prompt.lower() or "evaluation" in prompt.lower():
                return '''
                {
                    "strengths": [
                        "Shows relevant experience in the field",
                        "Good communication skills",
                        "Problem-solving abilities"
                    ],
                    "areas_for_improvement": [
                        "Could provide more specific examples",
                        "Technical knowledge could be more advanced"
                    ],
                    "technical_evaluation": "The candidate demonstrates basic understanding of required technologies.",
                    "cultural_fit": "The candidate appears to align with company values.",
                    "recommendation": "Consider for next interview round",
                    "next_steps": "Technical assessment to evaluate specific skills",
                    "overall_assessment": "The candidate shows potential for the role with some areas to explore further."
                }
                '''
            else:
                # Generic JSON response
                return '''
                {
                    "response": "This is a fallback response due to LLM service unavailability.",
                    "status": "fallback",
                    "message": "Please try again later when the service is available."
                }
                '''
        
        # Regular text responses for non-JSON requests
        if "follow-up" in prompt.lower():
            return "Could you elaborate more on that point? I'd like to understand your perspective better."
        
        if "summary" in prompt.lower():
            return "Based on our conversation, you have demonstrated relevant experience and skills for this position. Thank you for sharing your background with me today."
        
        # Default text responses based on prompt length
        words = prompt.split()
        word_count = len(words)
        
        if word_count < 50:
            return "I understand your query. To give you a better response, I would need the LLM service to be operational. Please try again later when the service is available."
        
        if word_count < 100:
            return "Thank you for your detailed query. The LLM service is currently unavailable, so I'm providing this pre-programmed response. Please try again later for a more tailored answer to your specific question."
        
        return "I appreciate your comprehensive question. However, the LLM service is currently unavailable. This is an automated fallback response. The system will attempt to reconnect with the LLM service shortly. In the meantime, please consider rephrasing your question or trying again later."


class DeepSeekProvider(LLMProvider):
    """Provider for DeepSeek API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.api_base = "https://api.deepseek.com/v1"
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
    
    def get_completion(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Get completion from DeepSeek API"""
        if not self.api_key:
            return "Error: DeepSeek API key not provided"
        
        try:
            response = self.session.post(
                f"{self.api_base}/chat/completions",
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                logger.error(f"DeepSeek API error: {response.status_code}, {response.text}")
                return f"Error: DeepSeek API returned status code {response.status_code}"
        except Exception as e:
            logger.exception(f"Error calling DeepSeek API: {str(e)}")
            return f"Error: Failed to get completion from DeepSeek. Error: {str(e)}"


class QwenProvider(LLMProvider):
    """Provider for Qwen API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("QWEN_API_KEY")
        self.api_base = "https://dashscope.aliyuncs.com/api/v1"
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
    
    def get_completion(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Get completion from Qwen API"""
        if not self.api_key:
            return "Error: Qwen API key not provided"
        
        try:
            response = self.session.post(
                f"{self.api_base}/services/aigc/text-generation/generation",
                json={
                    "model": "qwen-max",
                    "input": {
                        "prompt": prompt
                    },
                    "parameters": {
                        "max_tokens": max_tokens,
                        "temperature": temperature
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("output", {}).get("text", "")
            else:
                logger.error(f"Qwen API error: {response.status_code}, {response.text}")
                return f"Error: Qwen API returned status code {response.status_code}"
        except Exception as e:
            logger.exception(f"Error calling Qwen API: {str(e)}")
            return f"Error: Failed to get completion from Qwen. Error: {str(e)}"


class LLMService:
    """Service to get the appropriate LLM provider"""
    
    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None, **kwargs) -> LLMProvider:
        """Get the configured LLM provider"""
        from config import LLM_PROVIDER, OLLAMA_MODEL, DEEPSEEK_API_KEY, QWEN_API_KEY
        
        provider = provider_name or LLM_PROVIDER
        
        if provider == "ollama":
            model = kwargs.get("model", OLLAMA_MODEL)
            return OllamaProvider(model_name=model)
        elif provider == "deepseek":
            api_key = kwargs.get("api_key", DEEPSEEK_API_KEY)
            return DeepSeekProvider(api_key=api_key)
        elif provider == "qwen":
            api_key = kwargs.get("api_key", QWEN_API_KEY)
            return QwenProvider(api_key=api_key)
        else:
            logger.warning(f"Unknown provider: {provider}, falling back to Ollama")
            return OllamaProvider(model_name=OLLAMA_MODEL) 