import logging

logger = logging.getLogger(__name__)

class DocSearchTool:
    """Tool for searching documents sumbitted by users."""

    def __init__(self):
        """Initialize the document search tool."""
        super().__init__(
            name="doc_search",
            description="Searches documents submitted by users for relevant information.",
        )