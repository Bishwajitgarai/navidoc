from typing import Dict, Any, List

class PageIndex:
    def __init__(self):
        self.pages = []

    def load_pages(self, pages_data: List[Dict[str, Any]]):
        """Load the pages."""
        self.pages = pages_data

    def search(self, query: str) -> str:
        """
        Search the pages for relevant content.
        """
        # Skeleton: Return the whole content for now
        return f"PageIndex search for: {query}"
        
    def get_all_text(self) -> str:
        """Helper to get all text from pages."""
        return "\n".join([p.get("content", "") for p in self.pages])
