import os
import json
import subprocess
import platform
from typing import Optional, Dict, Any, List
import ollama

from .parsers.markdown import MarkdownParser
from .parsers.pdf import PdfParser
from .parsers.docx import DocxParser
from .parsers.pptx import PptxParser
from .index.tree import TreeIndex
from .index.page import PageIndex

class NaviDoc:
    def __init__(self, model: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize NaviDoc SDK.
        
        Priority for model selection:
        1. Explicitly passed `model` argument.
        2. `NAVIDOC_MODEL_NAME` environment variable.
        3. Fallback default 'phi3'.
        
        Priority for cache directory:
        1. Explicitly passed `cache_dir` argument.
        2. `NAVIDOC_CACHE_DIR` environment variable.
        3. Fallback default 'storage'.
        """
        self.model = model or os.getenv("NAVIDOC_MODEL_NAME", "phi3")
        self.cache_dir = cache_dir or os.getenv("NAVIDOC_CACHE_DIR", "storage")
        self.index = None
        self.index_type = None # "tree" or "page"
        self.history: List[Dict[str, str]] = [] # Chat history
        
        print(f"NaviDoc SDK initialized.")
        print(f"Model: {self.model}")
        print(f"Cache Dir: {self.cache_dir}")
        
        # Self-healing: Check Ollama and pull model if missing
        self._ensure_ollama_and_model()

    def _ensure_ollama_and_model(self):
        """Check if Ollama is running and pull the model if not present."""
        try:
            models_response = ollama.list()
            pulled_models = [m['name'] for m in models_response.get('models', [])]
            
            found = False
            for m in pulled_models:
                if m == self.model or m.startswith(self.model + ":"):
                    found = True
                    break
                    
            if not found:
                print(f"Model '{self.model}' not found locally. Pulling it now... (This may take a while)")
                ollama.pull(self.model)
                print(f"Successfully pulled {self.model}")
                
        except Exception as e:
            print(f"\n⚠️ Warning: Could not connect to Ollama.")
            print(f"Please ensure the Ollama service is running on your machine.")
            print(f"You can try calling `engine.start_ollama()` to start it.")
            print(f"Details: {e}\n")

    def start_ollama(self):
        """Try to start the Ollama service in the background."""
        print("Attempting to start Ollama service...")
        system = platform.system()
        try:
            if system == "Windows":
                # Use CREATE_NO_WINDOW to avoid popping up a cmd window
                subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Ollama start command issued.")
        except Exception as e:
            print(f"Failed to start Ollama: {e}")

    def stop_ollama(self):
        """Try to stop the Ollama service."""
        print("Attempting to stop Ollama service...")
        system = platform.system()
        try:
            if system == "Windows":
                subprocess.run(["taskkill", "/IM", "ollama.exe", "/F"], capture_output=True)
            else:
                subprocess.run(["pkill", "ollama"], capture_output=True)
            print("Ollama stop command issued.")
        except Exception as e:
            print(f"Failed to stop Ollama: {e}")

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

    def save_index(self, file_name: str):
        """Save the current index to the cache directory."""
        if not self.index:
            raise ValueError("No index to save. Ingest a document first.")
            
        data = {
            "index_type": self.index_type,
            "tree": self.index.tree if self.index_type == "tree" else None,
            "pages": self.index.pages if self.index_type == "page" else None
        }
        
        file_path = os.path.join(self.cache_dir, file_name)
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Index successfully saved to {file_path}")

    def load_index(self, file_name: str):
        """Load a previously saved index from the cache directory."""
        file_path = os.path.join(self.cache_dir, file_name)
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

        if self.index_type == "tree":
            relevant_content = self._navigate_tree(prompt, self.index.tree)
        else:
            relevant_content = self.index.get_all_text()

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
            
            self.history.append({"user": prompt, "assistant": reply})
            
            return reply
        except Exception as e:
            return f"Error calling Ollama: {str(e)}"

    def clear_history(self):
        """Clear the chat history."""
        self.history = []
        print("Chat history cleared.")
