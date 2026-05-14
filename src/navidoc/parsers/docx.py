from docx import Document
from typing import Dict, Any, List

class DocxParser:
    def __init__(self):
        pass

    def parse(self, file_path: str) -> Dict[str, Any]:
        """Parse a DOCX file into a tree structure based on Heading styles."""
        doc = Document(file_path)
        
        root = {"title": "Root", "level": 0, "content": "", "children": []}
        stack = [root]
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
                
            style_name = para.style.name if para.style else ""
            
            # Check if it's a heading
            if style_name.startswith('Heading'):
                try:
                    # Extract level from "Heading 1" -> 1
                    level = int(style_name.split()[-1])
                except (ValueError, IndexError):
                    level = 1 # Fallback
                    
                node = {
                    "title": text,
                    "level": level,
                    "content": "",
                    "children": []
                }
                
                # Pop from stack until we find the parent
                while stack and stack[-1]["level"] >= level:
                    stack.pop()
                    
                if stack:
                    stack[-1]["children"].append(node)
                    stack.append(node)
                else:
                    root["children"].append(node)
                    stack.append(node)
            else:
                # Add content to the current node
                if stack:
                    stack[-1]["content"] += text + "\n"
                    
        return root
