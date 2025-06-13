"""Tool manager for registering and executing tools."""

import logging
from typing import Dict, List, Any, Optional
from .base_tool import BaseTool
from .response_parser import ResponseParser

logger = logging.getLogger(__name__)


class ToolManager:
    """Manages tool registration and execution for agents."""
    
    def __init__(self):
        """Initialize the tool manager."""
        self.tools: Dict[str, BaseTool] = {}
        self.parser = ResponseParser()
        self.logger = logging.getLogger(__name__)
        self.config = {
            "max_tool_calls_per_response": 2,
            "tool_timeout": 10,
            "fallback_on_error": True
        }
    
    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool with the manager.
        
        Args:
            tool: The tool instance to register
        """
        tool_name = tool.name.lower()
        self.tools[tool_name] = tool
        self.logger.info(f"Registered tool: {tool_name}")
    
    def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool from the manager.
        
        Args:
            tool_name: Name of the tool to unregister
            
        Returns:
            True if tool was unregistered, False if not found
        """
        tool_name = tool_name.lower()
        if tool_name in self.tools:
            del self.tools[tool_name]
            self.logger.info(f"Unregistered tool: {tool_name}")
            return True
        return False
    
    def get_available_tools(self) -> Dict[str, BaseTool]:
        """Get all available tools.
        
        Returns:
            Dictionary mapping tool names to tool instances
        """
        return self.tools.copy()
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all registered tools.
        
        Returns:
            List of tool schema dictionaries
        """
        return [tool.get_schema() for tool in self.tools.values()]
    
    def execute_tool(self, tool_name: str, **kwargs) -> List[str]:
        """Execute a specific tool with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Parameters to pass to the tool
            
        Returns:
            List of strings containing tool results
        """
        tool_name = tool_name.lower()
        
        if tool_name not in self.tools:
            error_msg = f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}"
            self.logger.error(error_msg)
            return [error_msg]
        
        tool = self.tools[tool_name]
        return tool.safe_execute(**kwargs)
    
    def process_response_with_tools(self, response: str) -> str:
        """Process a response, executing any tool calls found.
        
        Args:
            response: The original LLM response
            
        Returns:
            Enhanced response with tool results incorporated
        """
        # Parse the response for tool calls
        cleaned_response, tool_calls = self.parser.parse_response(response)
        
        if not tool_calls:
            return response
        
        # Limit the number of tool calls
        if len(tool_calls) > self.config["max_tool_calls_per_response"]:
            self.logger.warning(f"Too many tool calls ({len(tool_calls)}), limiting to {self.config['max_tool_calls_per_response']}")
            tool_calls = tool_calls[:self.config["max_tool_calls_per_response"]]
        
        # Execute tool calls and collect results
        tool_results = {}
        
        for tool_call in tool_calls:
            tool_name = tool_call["tool_name"]
            parameters = tool_call["parameters"]
            
            # Log tool execution start
            print(f"🔧 [TOOL MANAGER] Executing {tool_name} with params: {parameters}")
            self.logger.info(f"Executing tool: {tool_name} with parameters: {parameters}")
            
            try:
                results = self.execute_tool(tool_name, **parameters)
                tool_results[tool_name] = results
                print(f"✅ [TOOL MANAGER] {tool_name} completed successfully")
                
            except Exception as e:
                error_msg = f"Error executing {tool_name}: {str(e)}"
                self.logger.error(error_msg)
                print(f"❌ [TOOL MANAGER] {tool_name} failed: {str(e)}")
                if self.config["fallback_on_error"]:
                    tool_results[tool_name] = [error_msg]
        
        # Format and incorporate tool results
        if tool_results:
            formatted_results = self.parser.format_tool_results(tool_results)
            if formatted_results:
                # Add tool results before the main response
                enhanced_response = f"{formatted_results}\n\n{cleaned_response}"
                return enhanced_response.strip()
        
        return cleaned_response
    def is_tool_available(self, tool_name: str) -> bool:
        """Check if a tool is available.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            True if tool is available, False otherwise
        """
        return tool_name.lower() in self.tools
    
    def get_tool_count(self) -> int:
        """Get the number of registered tools.
        
        Returns:
            Number of registered tools
        """
        return len(self.tools)
    
    def update_config(self, **config_updates) -> None:
        """Update tool manager configuration.
        
        Args:
            **config_updates: Configuration parameters to update
        """
        self.config.update(config_updates)
        self.logger.info(f"Updated tool manager config: {config_updates}")


# Global tool manager instance
_tool_manager_instance = None


def get_tool_manager() -> ToolManager:
    """Get the global tool manager instance (singleton pattern).
    
    Returns:
        ToolManager instance
    """
    global _tool_manager_instance
    if _tool_manager_instance is None:
        _tool_manager_instance = ToolManager()
    return _tool_manager_instance