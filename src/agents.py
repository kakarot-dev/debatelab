"""Custom AutoGen agents that use the local GGUF model."""

import autogen
from typing import Dict, Any, Optional, List
import logging
from .llm_wrapper import get_llm
from .config import AGENT_PERSONALITIES, BASE_DEBATE_PROMPT, COLORS
from .tools.tool_manager import get_tool_manager
from .tools.builtin_tools.test_tool import TestTool
from .tools.builtin_tools.web_search_tool import WebSearchTool

logger = logging.getLogger(__name__)

class LocalLLMAgent(autogen.ConversableAgent):
    """Custom AutoGen agent that uses our local GGUF model."""
    
    def __init__(self, name: str, personality_key: str, **kwargs):
        """Initialize the local LLM agent.
        
        Args:
            name: Agent name
            personality_key: Key for personality configuration
            **kwargs: Additional agent parameters
        """
        self.personality_key = personality_key
        self.personality = AGENT_PERSONALITIES[personality_key]
        self.llm = get_llm()
        self.tool_manager = get_tool_manager()
        
        # Initialize tools if not already done
        self._initialize_tools()
        
        # Create system message with tool context
        combined_system_message = f"{self.personality['personality']}\n\n{BASE_DEBATE_PROMPT}"
        
        super().__init__(
            name=self.personality["name"],
            system_message=combined_system_message,
            llm_config=False,  # Disable default LLM config
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            **kwargs
        )
        
        # Override the generate_reply method to use our local LLM
        self._original_generate_reply = self.generate_reply
        self.register_reply([autogen.Agent, None], self._custom_generate_reply)
    
    def _custom_generate_reply(
        self,
        messages: Optional[List[Dict]] = None,
        sender: Optional[autogen.Agent] = None,
        config: Optional[Any] = None,
    ) -> tuple[bool, str]:
        """Custom reply generation using local LLM.
        
        Args:
            messages: Conversation messages
            sender: Sender agent
            config: Configuration
            
        Returns:
            Tuple of (success, response)
        """
        if not messages:
            return False, "No messages to process"
        
        try:
            # Prepare the conversation context
            conversation_context = self._prepare_context(messages)
            
            # Generate response using local LLM with function calling
            response = self.llm.create_chat_completion_with_tools(
                conversation_context,
                self.tool_manager,
                max_tool_calls=2
            )
            
            # Clean up the response
            response = self._clean_response(response)
            
            return True, response
            
        except Exception as e:
            logger.error(f"Error generating reply for {self.name}: {e}")
            return True, f"I'm having trouble formulating a response right now. Error: {str(e)}"
    
    def _prepare_context(self, messages: List[Dict]) -> List[Dict]:
        """Prepare conversation context for the LLM.
        
        Args:
            messages: Raw conversation messages
            
        Returns:
            Formatted messages for LLM
        """
        context = [{"role": "system", "content": self.system_message}]
        
        # Give agents access to more conversation history for better context
        # Use last 8 messages or all if fewer, but prioritize recent exchanges
        recent_messages = messages[-8:] if len(messages) > 8 else messages
        
        for msg in recent_messages:
            content = msg.get("content", "")
            if content and content.strip():
                # Determine role based on message structure
                if "name" in msg:
                    speaker_name = msg["name"]
                    if speaker_name == self.name:
                        context.append({"role": "assistant", "content": content})
                    else:
                        context.append({"role": "user", "content": f"{speaker_name}: {content}"})
                else:
                    context.append({"role": "user", "content": content})
        
        return context
    
    def _clean_response(self, response: str) -> str:
        """Clean and format the response.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            Cleaned response
        """
        response = response.strip()
        
        if response.startswith(f"{self.name}:"):
            response = response[len(f"{self.name}:"):].strip()
        
        artifacts = ["<|assistant|>", "<|human|>", "<|system|>", "<|user|>", "<|end|>", "Assistant:", "Human:", "System:", "\n\nHuman:", "\n\nAssistant:"]
        for artifact in artifacts:
            if response.startswith(artifact):
                response = response[len(artifact):].strip()
            if response.endswith(artifact):
                response = response[:-len(artifact)].strip()
        
        import re
        response = re.sub(r'\[.*?\]', '', response)
        response = re.sub(r'\(.*?\)', '', response)
        response = re.sub(r'\{.*?\}', '', response)
        
        response = re.sub(r'\b(?:generated|word count|words?|tokens?|characters?)\s*:?\s*\d+\b', '', response, flags=re.IGNORECASE)
        response = re.sub(r'\b\d+\s*(?:words?|tokens?|characters?)\s*(?:generated|produced|written)?\b', '', response, flags=re.IGNORECASE)
        
        lines = response.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Skip lines that look like metadata
            if (re.match(r'^\d+\s*(?:words?|tokens?|characters?)', line, re.IGNORECASE) or
                re.match(r'^(?:generated|word count|tokens?|characters?)\s*:?\s*\d+', line, re.IGNORECASE) or
                re.match(r'^(?:time|duration|elapsed)\s*:?\s*\d+', line, re.IGNORECASE)):
                continue
            cleaned_lines.append(line)
        
        response = '\n'.join(cleaned_lines)
        
        response = re.sub(r'\s+', ' ', response).strip()
        
        return response
    
    def get_color(self) -> str:
        return COLORS.get(self.personality["color"], COLORS["white"])
    
    def _initialize_tools(self):
        """Initialize tools for the agent if not already done."""
        if self.tool_manager.get_tool_count() == 0:
            # Register the test tool
            test_tool = TestTool()
            self.tool_manager.register_tool(test_tool)
            
            # Register the web search tool
            web_search_tool = WebSearchTool()
            self.tool_manager.register_tool(web_search_tool)
            
            logger.info("Initialized tools for agents: test_tool, web_search")
            print("🔧 [TOOLS] Registered tools: test_tool, web_search")

class DebateAgentFactory:
    """Factory for creating debate agents."""
    
    @staticmethod
    def create_agent(personality_key: str) -> LocalLLMAgent:
        """Create an agent with the specified personality.
        
        Args:
            personality_key: Key for the personality configuration
            
        Returns:
            Configured LocalLLMAgent
        """
        if personality_key not in AGENT_PERSONALITIES:
            raise ValueError(f"Unknown personality: {personality_key}")
        
        return LocalLLMAgent(
            name=AGENT_PERSONALITIES[personality_key]["name"],
            personality_key=personality_key
        )
    
    @staticmethod
    def create_all_agents() -> Dict[str, LocalLLMAgent]:
        """Create all available agents.
        
        Returns:
            Dictionary mapping personality keys to agents
        """
        agents = {}
        for personality_key in AGENT_PERSONALITIES:
            if personality_key not in ["moderator", "judge"]:  # Create moderator and judge separately if needed
                agents[personality_key] = DebateAgentFactory.create_agent(personality_key)
        return agents
    
    @staticmethod
    def create_judge() -> LocalLLMAgent:
        """Create the judge agent.
        
        Returns:
            Configured judge agent
        """
        return DebateAgentFactory.create_agent("judge")
    
    @staticmethod
    def create_moderator() -> LocalLLMAgent:
        """Create the moderator agent.
        
        Returns:
            Configured moderator agent
        """
        return DebateAgentFactory.create_agent("moderator")