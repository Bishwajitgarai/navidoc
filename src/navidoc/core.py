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
from .db import Database

class NaviDoc:
    def __init__(self, model: Optional[str] = None, cache_dir: Optional[str] = None, session_id: str = "default", enable_db: bool = True, max_history: int = 10):
        """
        Initialize NaviDoc SDK.
        
        :param model: Ollama model name (default: 'phi3')
        :param cache_dir: Directory for storage (default: 'storage')
        :param session_id: Session ID for chat history
        :param enable_db: Whether to use SQLite for chat storage
        :param max_history: Maximum number of chat turns to keep in context
        """
        self.model = model or os.getenv("NAVIDOC_MODEL_NAME", "phi3")
        self.cache_dir = cache_dir or os.getenv("NAVIDOC_CACHE_DIR", "storage")
        self.session_id = session_id
        self.enable_db = enable_db
        self.max_history = max_history
        
        self.index = None
        self.index_type = None # "tree" or "page"
        
        print(f"NaviDoc SDK initialized.")
        print(f"Model: {self.model}")
        print(f"Cache Dir: {self.cache_dir}")
        print(f"Session ID: {self.session_id}")
        print(f"History Limit: {self.max_history} turns")
        
        # Initialize SQLite Database if enabled
        if self.enable_db:
            db_path = os.path.join(self.cache_dir, "navidoc.db")
            self.db = Database(db_path)
        else:
            self.db = None
            self.history: List[Dict[str, str]] = []
            
        # Check Ollama status on init
        if self.is_ollama_running():
            print("Ollama service: Connected")
            self._ensure_model_exists()
        else:
            print("\n⚠️ Warning: Could not connect to Ollama.")
            print("Please ensure the Ollama service is running on your machine.")
            print("You can try calling `engine.start_ollama()` to start it.\n")

    def is_ollama_running(self) -> bool:
        """Check if the Ollama service is running and accessible."""
        try:
            ollama.list()
            return True
        except Exception:
            return False

    def _ensure_model_exists(self):
        """Pull the model if it is not present locally."""
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
            else:
                print(f"Model '{self.model}' is ready.")
                
        except Exception as e:
            print(f"Error checking/pulling model: {e}")

    def start_ollama(self):
        """Try to start the Ollama service in the background."""
        print("Attempting to start Ollama service...")
        system = platform.system()
        try:
            if system == "Windows":
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
            
        elif ext in ['.png', '.jpg', '.jpeg']:
            try:
                from glmocr import parse
                print(f"Using GLM-OCR to parse image: {file_path}")
                result = parse(file_path)
                text = getattr(result, 'markdown', str(result))
                
                temp_md_path = os.path.join(self.cache_dir, "temp_ocr.md")
                os.makedirs(os.path.dirname(temp_md_path), exist_ok=True)
                with open(temp_md_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                parser = MarkdownParser()
                tree_data = parser.parse(temp_md_path)
                
                self.index = TreeIndex()
                self.index.load_tree(tree_data)
                self.index_type = "tree"
                
                try:
                    os.remove(temp_md_path)
                except:
                    pass
                    
                return f"Successfully ingested Image via GLM-OCR: {file_path}"
                
            except ImportError:
                return "Error: 'glmocr' is not installed. Please run `pip install glmocr` to enable image support."
            except Exception as e:
                return f"Error during OCR processing: {e}"
            
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

    def _verify_relevance(self, query: str, content: str) -> bool:
        """Ask the LLM if the content is relevant to the query."""
        prompt = f"""
Given the user query: "{query}"
And the following content:
\"\"\"
{content}
\"\"\"

Does this content contain information to answer the query?
Reply ONLY with 'YES' or 'NO'.
"""
        try:
            response = ollama.generate(model=self.model, prompt=prompt)
            answer = response['response'].strip().upper()
            return 'YES' in answer
        except Exception:
            return True # Fallback to assuming relevant if error

    def _navigate_tree(self, query: str, node: Dict[str, Any]) -> str:
        """Recursively navigate the tree using the local LLM."""
        if not node.get("children"):
            content = node.get("content", "")
            # Check relevance at leaf node!
            if self._verify_relevance(query, content):
                return content
            else:
                return "NOT_RELEVANT"

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
                    result = self._navigate_tree(query, child)
                    if result == "NOT_RELEVANT":
                        # If the best child was not relevant, fall back to the parent content!
                        print(f"Notice: Leaf node in '{chosen_header}' was not relevant. Falling back to parent content.")
                        return node.get("content", "Content not found.")
                    return result
                    
            return node.get("content", "Navigation path lost.")
            
        except Exception as e:
            return f"Navigation error: {str(e)}"

    def query(self, prompt: str) -> str:
        """One-off query without maintaining history."""
        if not self.index:
            return "No document ingested yet."

        if self.index_type == "tree":
            relevant_content = self._navigate_tree(prompt, self.index.tree)
            if relevant_content == "NOT_RELEVANT":
                relevant_content = self.index.tree.get("content", "No relevant content found.")
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
            if relevant_content == "NOT_RELEVANT":
                relevant_content = self.index.tree.get("content", "No relevant content found.")
        else:
            relevant_content = self.index.get_all_text()

        # Load history
        if self.enable_db and self.db:
            history = self.db.load_chat(self.session_id)
        else:
            history = self.history

        # Apply History Limit
        if len(history) > self.max_history:
            history = history[-self.max_history:]

        history_str = ""
        for turn in history:
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
            
            # Save history
            if self.enable_db and self.db:
                self.db.save_chat(self.session_id, prompt, reply)
            else:
                self.history.append({"user": prompt, "assistant": reply})
            
            return reply
        except Exception as e:
            return f"Error calling Ollama: {str(e)}"

    def clear_history(self):
        """Clear the chat history for the current session."""
        if self.enable_db and self.db:
            self.db.clear_chat(self.session_id)
        else:
            self.history = []
        print(f"Chat history cleared.")
        
    def get_db_path(self) -> str:
        """Return the path to the SQLite database if enabled, otherwise 'not'."""
        if self.enable_db:
            return os.path.join(self.cache_dir, "navidoc.db")
        else:
            return "not"
