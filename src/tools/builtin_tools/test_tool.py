"""Test tool for demonstrating the tool framework."""

from typing import List, Dict, Any
from ..base_tool import BaseTool


class TestTool(BaseTool):
    """A test tool that returns sample data for demonstration purposes."""
    
    def __init__(self):
        """Initialize the test tool."""
        super().__init__(
            name="test_tool",
            description="A test tool that returns sample information based on a query. Useful for testing the tool framework."
        )
    
    def execute(self, query: str = "", topic: str = "") -> List[str]:
        """Execute the test tool.
        
        Args:
            query: The query string to process
            topic: Optional topic for more specific results
            
        Returns:
            List of sample results
        """
        # Use topic if provided, otherwise use query
        search_term = topic if topic else query
        
        if not search_term:
            return [
                "Test tool executed successfully",
                "No specific query provided - returning general test data",
                "This demonstrates the tool framework is working"
            ]
        
        # Generate contextual test results based on the search term
        results = []
        
        # Add a primary result
        results.append(f"Test result for '{search_term}': Primary information found")
        
        # Add topic-specific mock data
        if any(keyword in search_term.lower() for keyword in ['climate', 'environment', 'renewable', 'energy']):
            results.extend([
                "Environmental data: Global renewable energy capacity increased by 12% in 2023",
                "Climate statistics: Carbon emissions from renewable sources decreased by 8%",
                "Policy update: 15 countries announced new green energy initiatives"
            ])
        elif any(keyword in search_term.lower() for keyword in ['ai', 'artificial', 'intelligence', 'technology']):
            results.extend([
                "AI research: Machine learning models showed 25% improvement in efficiency",
                "Technology trends: AI adoption in education increased by 40% this year",
                "Industry report: 78% of companies plan to integrate AI tools by 2025"
            ])
        elif any(keyword in search_term.lower() for keyword in ['economy', 'economic', 'finance', 'market']):
            results.extend([
                "Economic indicator: GDP growth rate stabilized at 2.3% this quarter",
                "Market analysis: Technology sector outperformed by 15%",
                "Financial report: Consumer spending increased by 5% year-over-year"
            ])
        elif any(keyword in search_term.lower() for keyword in ['health', 'medical', 'healthcare', 'medicine']):
            results.extend([
                "Health statistics: Preventive care adoption increased by 30%",
                "Medical research: New treatment protocols showed 85% success rate",
                "Healthcare policy: Universal coverage expanded to 3 additional regions"
            ])
        else:
            # Generic results for other topics
            results.extend([
                f"Statistical data related to '{search_term}' shows positive trends",
                f"Recent studies on '{search_term}' indicate significant developments",
                f"Expert analysis suggests '{search_term}' will continue to evolve"
            ])
        
        # Add a timestamp-like result
        results.append("Data retrieved: Current information as of latest available sources")
        
        return results
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get the parameters schema for this tool.
        
        Returns:
            Dictionary describing the tool's parameters
        """
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query or topic to get test information about"
                },
                "topic": {
                    "type": "string",
                    "description": "Optional specific topic for more targeted results"
                }
            },
            "required": []
        }
    
    def validate_params(self, **kwargs) -> bool:
        """Validate the provided parameters.
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        # For the test tool, we accept any parameters or no parameters
        # This makes it very flexible for testing
        return True