"""LLM wrapper for interfacing with the local GGUF model."""

from llama_cpp import Llama
from typing import Optional, Dict, Any
import logging
from .config import MODEL_CONFIG

logger = logging.getLogger(__name__)

class LocalLLM:
    """Wrapper for the local GGUF model using llama-cpp-python."""
    
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        """Initialize the local LLM.
        
        Args:
            model_config: Configuration dictionary for the model
        """
        self.config = model_config or MODEL_CONFIG
        self.llm = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Llama model."""
        try:
            logger.info(f"Loading model from {self.config['model_path']}")
            self.llm = Llama(
                model_path=self.config["model_path"],
                n_ctx=self.config["n_ctx"],
                n_threads=self.config["n_threads"],
                verbose=self.config["verbose"]
            )
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a response from the model.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Generated response text
        """
        if not self.llm:
            raise RuntimeError("Model not initialized")
        
        # Merge kwargs with default config
        generation_params = {
            "max_tokens": self.config["max_tokens"],
            "temperature": self.config["temperature"],
            "top_p": self.config["top_p"],
            "top_k": self.config["top_k"],
            "repeat_penalty": self.config["repeat_penalty"],
            "stop": ["\n\nHuman:", "\n\nAssistant:", "Human:", "Assistant:"],
            **kwargs
        }
        
        try:
            response = self.llm(prompt, **generation_params)
            text = response["choices"][0]["text"].strip()
            
            # Clean up any system artifacts or unwanted text
            # Only include patterns that are clearly meta-commentary or system artifacts
            unwanted_patterns = [
                "System:", "Human:", "Assistant:", "User:",
                "Agent Response:", "Agents Response:", "Agent's Response:",
                "The agent responds:", "The character says:",
                "Here is the response:", "Here's the response:",
                "This section is more human like",
                "Thank you for bringing up valid concerns. Let's continue this conversatio",
                "System: Thank you for bringing up valid concerns",
                "Let's continue this conversatio"
            ]
            
            for pattern in unwanted_patterns:
                # Only match patterns at the beginning of the text or after newlines
                # to avoid cutting off legitimate content that contains these phrases
                if text.startswith(pattern) or f"\n{pattern}" in text:
                    if text.startswith(pattern):
                        text = text[len(pattern):].strip()
                    else:
                        text = text.split(f"\n{pattern}")[0].strip()
            
            # # Only do minimal cleanup - don't cut off responses aggressively
            # if text and text.endswith(','):
            #     # If ends with comma, replace with period
            #     text = text[:-1] + '.'
            # elif text and not text.endswith(('.', '!', '?', ':')):
            #     # Only add period if it doesn't end with any punctuation
            #     text += '.'
            
            return text
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error: Could not generate response - {str(e)}"
    
    def create_chat_completion(self, messages: list, **kwargs) -> str:
        """Create a chat completion from a list of messages.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional generation parameters
            
        Returns:
            Generated response text
        """
        # Convert messages to a single prompt
        prompt = self._messages_to_prompt(messages)
        return self.generate_response(prompt, **kwargs)
    
    def _messages_to_prompt(self, messages: list) -> str:
        """Convert a list of messages to a single prompt string.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)
    
    def is_available(self) -> bool:
        """Check if the model is available and ready.
        
        Returns:
            True if model is ready, False otherwise
        """
        return self.llm is not None

# Global instance
_llm_instance = None

def get_llm() -> LocalLLM:
    """Get the global LLM instance (singleton pattern).
    
    Returns:
        LocalLLM instance
    """
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LocalLLM()
    return _llm_instance