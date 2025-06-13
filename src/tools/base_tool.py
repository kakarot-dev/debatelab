"""Base tool class for the tool framework."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Abstract base class for all tools that agents can use."""
    
    def __init__(self, name: str, description: str):
        """Initialize the base tool.
        
        Args:
            name: Tool name (used for function calls)
            description: Tool description for LLM context
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def execute(self, **kwargs) -> List[str]:
        """Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            List of strings containing tool results
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool schema for LLM context.
        
        Returns:
            Dictionary containing tool schema information
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_parameters_schema()
        }
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get the parameters schema for this tool.
        
        Returns:
            Dictionary describing the tool's parameters
        """
        pass
    
    def validate_params(self, **kwargs) -> bool:
        """Validate the provided parameters.
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        # Default implementation - can be overridden by specific tools
        return True
    
    def safe_execute(self, **kwargs) -> List[str]:
        """Safely execute the tool with error handling.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            List of strings containing results or error messages
        """
        try:
            if not self.validate_params(**kwargs):
                return [f"Error: Invalid parameters for tool '{self.name}'"]
            
            self.logger.info(f"Executing tool '{self.name}' with params: {kwargs}")
            results = self.execute(**kwargs)
            
            if not isinstance(results, list):
                results = [str(results)]
            
            self.logger.info(f"Tool '{self.name}' returned {len(results)} results")
            return results
            
        except Exception as e:
            error_msg = f"Error executing tool '{self.name}': {str(e)}"
            self.logger.error(error_msg)
            return [error_msg]
    
    def __str__(self) -> str:
        return f"Tool({self.name}): {self.description}"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"