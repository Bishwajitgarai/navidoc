import os
import json
from typing import Optional, Dict, Any, List
import ollama

from .parsers.markdown import MarkdownParser
from .parsers.pdf import PdfParser
from .parsers.docx import DocxParser
from .parsers.pptx import PptxParser
from .index.tree import TreeIndex
from .index.page import PageIndex

class NaviDoc:
    def __init__(self, model: Optional[str] = None):
        """
        Initialize NaviDoc SDK.
        
        Priority for model selection:
        1. Explicitly passed `model` argument.
        2. `NAVIDOC_MODEL_NAME` environment variable.
        3. Fallback default 'phi3'.
        """
        self.model = model or os.getenv("NAVIDOC_MODEL_NAME", "phi3")
        self.index = None
        self.index_type = None # "tree" or "page"
        self.history: List[Dict[str, str]] = [] # Chat history
        
        print(f"NaviDoc SDK initialized with model: {self.model}")

    def ingest(self, file_path: str) -> str:
        """Ingest a document and create the appropriate index."""
        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found."

        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.md':
            parser = MarkdownParser()
            tree_data = parser.parse(file_path)
            self.index = TreeIndex()
            self.index.load_tree(tree_data)
            self.index_type = "tree"
            return f"Successfully ingested Markdown: {file_path}"
            
        elif ext == '.pdf':
            parser = PdfParser()
            tree_data = parser.parse(file_path)
            self.index = TreeIndex()
            self.index.load_tree(tree_data)
            self.index_type = "tree"
            return f"Successfully ingested PDF (Tree): {file_path}"
            
        elif ext == '.docx':
            parser = DocxParser()
            tree_data = parser.parse(file_path)
            self.index = TreeIndex()
            self.index.load_tree(tree_data)
            self.index_type = "tree"
            return f"Successfully ingested DOCX (Tree): {file_path}"
            
        elif ext == '.pptx':
            parser = PptxParser()
            pptx_data = parser.parse(file_path)
            self.index = PageIndex()
            self.index.load_pages(pptx_data["pages"])
            self.index_type = "page"
            return f"Successfully ingested PPTX: {file_path}"
            
        else:
            return f"Unsupported file format: {ext}"

    def ingest_markdown(self, file_path: str) -> str:
        """Explicit method for markdown as requested in README."""
        return self.ingest(file_path)

    def save_index(self, file_path: str):
        """Save the current index to a JSON file for fast reloading."""
        if not self.index:
            raise ValueError("No index to save. Ingest a document first.")
            
        data = {
            "index_type": self.index_type,
            "tree": self.index.tree if self.index_type == "tree" else None,
            "pages": self.index.pages if self.index_type == "page" else None
        }
        
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Index successfully saved to {file_path}")

    def load_index(self, file_path: str):
        """Load a previously saved index from a JSON file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Index file not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.index_type = data["index_type"]
        if self.index_type == "tree":
            self.index = TreeIndex()
            self.index.load_tree(data["tree"])
        elif self.index_type == "page":
            self.index = PageIndex()
            self.index.load_pages(data["pages"])
        print(f"Index successfully loaded from {file_path}")

    def _navigate_tree(self, query: str, node: Dict[str, Any]) -> str:
        """Recursively navigate the tree using the local LLM."""
        if not node.get("children"):
            return node.get("content", "")

        headers = [child["title"] for child in node["children"]]
        
        prompt = f"""
Given the query: "{query}"
And the following document sections:
{", ".join([f"'{h}'" for h in headers])}

Which section is most likely to contain the answer? 
Reply ONLY with the exact section title from the list above. If none seem relevant, reply 'NONE'.
"""
        try:
            response = ollama.generate(model=self.model, prompt=prompt)
            chosen_header = response['response'].strip().strip("'").strip('"')
            
            if chosen_header == 'NONE':
                return node.get("content", "Section not found.")
                
            for child in node["children"]:
                if child["title"] == chosen_header:
                    return self._navigate_tree(query, child)
                    
            return node.get("content", "Navigation path lost.")
            
        except Exception as e:
            return f"Navigation error: {str(e)}"

    def query(self, prompt: str) -> str:
        """One-off query without maintaining history."""
        if not self.index:
            return "No document ingested yet."

        if self.index_type == "tree":
            relevant_content = self._navigate_tree(prompt, self.index.tree)
        else:
            relevant_content = self.index.get_all_text()

        full_prompt = f"""
Answer the user's question based ONLY on this specific context found during navigation:
{relevant_content}

Question: {prompt}
Answer:
"""
        try:
            response = ollama.generate(model=self.model, prompt=full_prompt)
            return response['response']
        except Exception as e:
            return f"Error calling Ollama: {str(e)}"

    def chat(self, prompt: str) -> str:
        """Chat with the document, maintaining conversation history."""
        if not self.index:
            return "No document ingested yet."

        # Get context for the latest query
        if self.index_type == "tree":
            relevant_content = self._navigate_tree(prompt, self.index.tree)
        else:
            relevant_content = self.index.get_all_text()

        # Format history for Ollama
        history_str = ""
        for turn in self.history:
            history_str += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n"

        full_prompt = f"""
You are having a conversation about a document. 
Answer the user's latest question based ONLY on the context provided below.
Maintain continuity with the conversation history.

Context:
{relevant_content}

History:
{history_str}

User: {prompt}
Assistant:
"""
        try:
            response = ollama.generate(model=self.model, prompt=full_prompt)
            reply = response['response']
            
            # Save to history
            self.history.append({"user": prompt, "assistant": reply})
            
            return reply
        except Exception as e:
            return f"Error calling Ollama: {str(e)}"

    def clear_history(self):
        """Clear the chat history."""
        self.history = []
        print("Chat history cleared.")
