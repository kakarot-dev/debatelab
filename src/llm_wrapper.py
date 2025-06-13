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
            "stop": ["<|human|>", "<|assistant|>", "<|system|>", "<|end|>"],
            **kwargs
        }
        
        try:
            response = self.llm(prompt, **generation_params)
            text = response["choices"][0]["text"].strip()
            
            # Clean up any system artifacts or unwanted text
            # Only include patterns that are clearly meta-commentary or system artifacts
            unwanted_patterns = [
                "<|system|>", "<|human|>", "<|assistant|>", "<|user|>", "<|end|>",
                "System:", "Human:", "Assistant:", "User:",
                "Agent Response:", "Agents Response:", "Agent's Response:",
                "The agent responds:", "The character says:",
                "Here is the response:", "Here's the response:",
                "This section is more human like",
                "Thank you for bringing up valid concerns. Let's continue this conversatio",
                "System: Thank you for bringing up valid concerns",
                "Let's continue this conversatio",
                "---"
            ]
            
            for pattern in unwanted_patterns:
                # Only match patterns at the beginning of the text or after newlines
                # to avoid cutting off legitimate content that contains these phrases
                if text.startswith(pattern) or f"\n{pattern}" in text:
                    if text.startswith(pattern):
                        text = text[len(pattern):].strip()
                    else:
                        text = text.split(f"\n{pattern}")[0].strip()
            
            return text
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error: Could not generate response - {str(e)}"
    
    def create_chat_completion(self, messages: list, tools=None, **kwargs) -> str:
        """Create a chat completion from a list of messages.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            tools: Available tools for function calling
            **kwargs: Additional generation parameters
            
        Returns:
            Generated response text
        """
        # Convert messages to a single prompt
        prompt = self._messages_to_prompt(messages, tools)
        return self.generate_response(prompt, **kwargs)
    
    def _messages_to_prompt(self, messages: list, tools=None) -> str:
        """Convert a list of messages to a single prompt string.
        
        Args:
            messages: List of message dictionaries
            tools: Available tools for function calling
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"<|system|>\n{content}\n<|end|>")
            elif role == "user":
                prompt_parts.append(f"<|human|>\n{content}\n<|end|>")
            elif role == "assistant":
                prompt_parts.append(f"<|assistant|>\n{content}\n<|end|>")
            elif role == "tool":
                prompt_parts.append(f"<|tool_result|>\n{content}\n<|end|>")
        
        prompt_parts.append("<|assistant|>")
        return "\n\n".join(prompt_parts)
    
    def create_chat_completion_with_tools(self, messages: list, tool_manager, max_tool_calls=3) -> str:
        """Create a chat completion with intelligent tool usage.
        
        Args:
            messages: List of message dictionaries
            tool_manager: Tool manager instance
            max_tool_calls: Maximum number of tool calls to allow
            
        Returns:
            Final response after tool calls
        """
        tool_decision_messages = messages.copy()
        
        available_tools = tool_manager.get_available_tools()
        tool_list = "\n".join([f"- {name}: {tool.description}" for name, tool in available_tools.items()])
        
        tool_decision_messages.append({
            "role": "user",
            "content": f"""This is just a checking message if you need a tool for your next response

Available tools:
{tool_list}
You can use the following format to request a tool:
RESPOND WITH ONLY JSON - NO OTHER TEXT:

{{"need_tool": true, "tool_name": "tool", "query": "search terms"}}
OR
{{"need_tool": false}}"""
        })
        
        print("🤔 [TOOL DECISION] Asking LLM if it needs tools...")
        tool_decision = self.create_chat_completion(tool_decision_messages, stop=["response", "Solution"])
        print(tool_decision)
        print(f"🤔 [TOOL DECISION] LLM response: {tool_decision.strip()}")
        
        # Step 2: Parse the JSON decision
        try:
            import json
            
            json_str = tool_decision.strip()
            
            brace_count = 0
            start_idx = json_str.find('{')
            if start_idx != -1:
                for i, char in enumerate(json_str[start_idx:], start_idx):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = json_str[start_idx:i+1]
                            break
            
            decision_data = json.loads(json_str)
            print(f"🎯 [TOOL DECISION] Parsed JSON: {decision_data}")
            
            if decision_data.get("need_tool", False):
                tool_name = decision_data.get("tool_name", "web_search")
                query = decision_data.get("query", "general information")
                tool_calls = [{
                    "tool_name": tool_name.lower(),
                    "parameters": {"query": query}
                }]
                print(f"✅ [TOOL DECISION] Tool requested: {tool_name}(query='{query}')")
            else:
                tool_calls = []
                print("ℹ️ [TOOL DECISION] No tools needed")
                
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ [TOOL DECISION] JSON parsing failed: {e}")
            print(f"   Raw response: {tool_decision}")
            tool_calls = []
        
        # Step 3: Execute tools if requested
        if tool_calls:
            enhanced_messages = messages.copy()
            
            for tool_call in tool_calls:
                tool_name = tool_call["tool_name"]
                parameters = tool_call["parameters"]
                
                print(f"🔧 [TOOL EXECUTION] Executing {tool_name} with {parameters}")
                results = tool_manager.execute_tool(tool_name, **parameters)
                
                # Add tool results to context
                tool_content = f"[TOOL RESULTS from {tool_name}]\n" + "\n".join(f"• {result}" for result in results)
                enhanced_messages.append({
                    "role": "user",
                    "content": f"{tool_content}\n\nNow provide your debate response using this information."
                })
            
            # Step 4: Generate final response with tool context
            print("💬 [FINAL RESPONSE] Generating response with tool results...")
            print(enhanced_messages)
            return self.create_chat_completion(enhanced_messages)
            
        # Step 5: Generate response without tools
        print("💬 [FINAL RESPONSE] Generating response without tools...")
        print(messages)
        return self.create_chat_completion(messages)
    
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