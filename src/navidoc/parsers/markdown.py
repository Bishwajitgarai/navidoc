import re
from typing import List, Dict, Any

class MarkdownParser:
    def __init__(self):
        pass

    def parse(self, file_path: str) -> Dict[str, Any]:
        """Parse a markdown file into a tree structure based on headers."""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        root = {"title": "Root", "level": 0, "content": "", "children": []}
        stack = [root]

        for line in lines:
            match = re.match(r'^(#+)\s+(.*)', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                
                node = {
                    "title": title,
                    "level": level,
                    "content": "",
                    "children": []
                }
                
                # Pop from stack until we find the parent (level < current level)
                while stack and stack[-1]["level"] >= level:
                    stack.pop()
                
                if stack:
                    stack[-1]["children"].append(node)
                    stack.append(node)
                else:
                    # Fallback if somehow stack is empty
                    root["children"].append(node)
                    stack.append(node)
            else:
                # Add content to the current node
                if stack:
                    stack[-1]["content"] += line

        return root
