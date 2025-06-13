"""Response parser for detecting and extracting tool calls from LLM responses."""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ResponseParser:
    """Parser for extracting tool calls from LLM responses."""
    
    # Pattern to match TOOL_CALL: tool_name(param1="value1", param2="value2")
    TOOL_CALL_PATTERN = re.compile(
        r'TOOL_CALL:\s*(\w+)\s*\((.*?)\)',
        re.IGNORECASE | re.DOTALL
    )
    
    # Pattern to match malformed TOOL_CALL: tool_name followed by text
    MALFORMED_TOOL_PATTERN = re.compile(
        r'TOOL_CALL:\s*(\w+)\s+([^.!?]*?)(?:[.!?]|$)',
        re.IGNORECASE | re.DOTALL
    )
    
    # Alternative pattern for other formats the LLM might use
    ALT_TOOL_PATTERN = re.compile(
        r'(?:use|call|invoke)\s+(\w+)\s*(?:tool|function)?\s*(?:with|for)?\s*["\']([^"\']*)["\']',
        re.IGNORECASE
    )
    
    # Pattern to extract parameters from the function call
    PARAM_PATTERN = re.compile(
        r'(\w+)\s*=\s*["\']([^"\']*)["\']',
        re.IGNORECASE
    )
    
    def __init__(self):
        """Initialize the response parser."""
        self.logger = logging.getLogger(__name__)
    
    def parse_response(self, response: str) -> tuple[str, List[Dict[str, Any]]]:
        """Parse a response for tool calls.
        
        Args:
            response: The LLM response text
            
        Returns:
            Tuple of (cleaned_response, list_of_tool_calls)
        """
        tool_calls = []
        cleaned_response = response
        
        # Find all tool calls in the response using primary pattern
        matches = self.TOOL_CALL_PATTERN.findall(response)
        
        for tool_name, params_str in matches:
            try:
                # Parse parameters
                params = self._parse_parameters(params_str)
                
                tool_call = {
                    "tool_name": tool_name.lower(),
                    "parameters": params
                }
                
                tool_calls.append(tool_call)
                self.logger.info(f"Parsed tool call: {tool_name} with params: {params}")
                
            except Exception as e:
                self.logger.error(f"Error parsing tool call '{tool_name}': {e}")
                continue
        
        # If no primary matches found, try malformed pattern (TOOL_CALL: tool_name text)
        if not tool_calls:
            malformed_matches = self.MALFORMED_TOOL_PATTERN.findall(response)
            for tool_name, query_text in malformed_matches:
                if tool_name.lower() in ['web_search', 'websearch', 'search', 'test_tool', 'test']:
                    # Clean up the query text
                    query = query_text.strip()
                    tool_call = {
                        "tool_name": "web_search" if "search" in tool_name.lower() else "test_tool",
                        "parameters": {"query": query}
                    }
                    tool_calls.append(tool_call)
                    self.logger.info(f"Parsed malformed tool call: {tool_name} -> {tool_call}")
                    print(f"🔧 [PARSER] Fixed malformed tool call: TOOL_CALL: {tool_name} -> {tool_call}")
        
        # If still no matches, try alternative patterns
        if not tool_calls:
            alt_matches = self.ALT_TOOL_PATTERN.findall(response)
            for tool_name, query in alt_matches:
                if tool_name.lower() in ['web_search', 'websearch', 'search', 'test_tool', 'test']:
                    tool_call = {
                        "tool_name": "web_search" if "search" in tool_name.lower() else "test_tool",
                        "parameters": {"query": query}
                    }
                    tool_calls.append(tool_call)
                    self.logger.info(f"Parsed alternative tool call: {tool_name} -> {tool_call}")
        
        # Remove tool calls from the response text
        cleaned_response = self.TOOL_CALL_PATTERN.sub('', response).strip()
        cleaned_response = self.MALFORMED_TOOL_PATTERN.sub('', cleaned_response).strip()
        cleaned_response = self.ALT_TOOL_PATTERN.sub('', cleaned_response).strip()
        
        return cleaned_response, tool_calls
    
    def _parse_parameters(self, params_str: str) -> Dict[str, str]:
        """Parse parameter string into a dictionary.
        
        Args:
            params_str: String containing parameters like 'param1="value1", param2="value2"'
            
        Returns:
            Dictionary of parameter name-value pairs
        """
        params = {}
        
        if not params_str.strip():
            return params
        
        # Find all parameter matches
        param_matches = self.PARAM_PATTERN.findall(params_str)
        
        for param_name, param_value in param_matches:
            params[param_name] = param_value
        
        # Handle simple cases without quotes (for single parameters)
        if not params and params_str.strip():
            # Try to parse as a single quoted string
            simple_match = re.match(r'^["\']([^"\']*)["\']$', params_str.strip())
            if simple_match:
                params['query'] = simple_match.group(1)
            else:
                # Fallback: treat the whole string as a query parameter
                params['query'] = params_str.strip().strip('"\'')
        
        return params
    
    def has_tool_calls(self, response: str) -> bool:
        """Check if a response contains tool calls.
        
        Args:
            response: The response text to check
            
        Returns:
            True if tool calls are found, False otherwise
        """
        return bool(self.TOOL_CALL_PATTERN.search(response))
    
    def extract_tool_names(self, response: str) -> List[str]:
        """Extract just the tool names from a response.
        
        Args:
            response: The response text
            
        Returns:
            List of tool names found in the response
        """
        matches = self.TOOL_CALL_PATTERN.findall(response)
        return [tool_name.lower() for tool_name, _ in matches]
    
    def format_tool_results(self, tool_results: Dict[str, List[str]]) -> str:
        """Format tool results for inclusion in agent response.
        
        Args:
            tool_results: Dictionary mapping tool names to their results
            
        Returns:
            Formatted string containing tool results
        """
        if not tool_results:
            return ""
        
        formatted_parts = []
        
        for tool_name, results in tool_results.items():
            if results:
                formatted_parts.append(f"[{tool_name.upper()} RESULTS]")
                for i, result in enumerate(results, 1):
                    formatted_parts.append(f"• {result}")
                formatted_parts.append("")  # Empty line for spacing
        
        return "\n".join(formatted_parts).strip()