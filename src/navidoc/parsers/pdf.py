from pypdf import PdfReader
from typing import Dict, Any, List

class PdfParser:
    def __init__(self):
        pass

    def parse(self, file_path: str) -> Dict[str, Any]:
        """Parse a PDF file into a tree structure based on font sizes."""
        reader = PdfReader(file_path)
        
        # 1. Analyze font sizes to find body and headings
        font_sizes = {}
        
        def size_visitor(text, cm, tm, font_dict, font_size):
            if text.strip():
                font_sizes[font_size] = font_sizes.get(font_size, 0) + len(text)

        for page in reader.pages:
            page.extract_text(visitor_text=size_visitor)
            
        if not font_sizes:
            return {"title": "Root", "level": 0, "content": "No text found", "children": []}
            
        # Body text is the most common font size
        body_size = max(font_sizes, key=font_sizes.get)
        
        # Headings are larger than body text
        headings = [s for s in font_sizes.keys() if s > body_size + 1.0]
        headings.sort(reverse=True)
        
        # Map font sizes to heading levels (up to 3 levels)
        heading_map = {}
        for i, size in enumerate(headings[:3]):
            heading_map[size] = i + 1
            
        # 2. Build the tree
        root = {"title": "Root", "level": 0, "content": "", "children": []}
        stack = [root]
        
        def build_visitor(text, cm, tm, font_dict, font_size):
            t = text.strip()
            if not t:
                return
                
            level = heading_map.get(font_size)
            if level:
                node = {
                    "title": t,
                    "level": level,
                    "content": "",
                    "children": []
                }
                
                # Pop stack until we find the parent
                while stack and stack[-1]["level"] >= level:
                    stack.pop()
                    
                if stack:
                    stack[-1]["children"].append(node)
                    stack.append(node)
                else:
                    root["children"].append(node)
                    stack.append(node)
            else:
                # Add text to the current node
                if stack:
                    stack[-1]["content"] += text + " "

        for page in reader.pages:
            page.extract_text(visitor_text=build_visitor)
            
        return root
