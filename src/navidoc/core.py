import os
import json
import subprocess
import platform
from typing import Optional, Dict, Any, List
import ollama
import numpy as np

from .parsers.markdown import MarkdownParser
from .parsers.pdf import PdfParser
from .parsers.docx import DocxParser
from .parsers.pptx import PptxParser
from .index.tree import TreeIndex
from .index.page import PageIndex
from .db import Database

class NaviDoc:
    def __init__(self, model: Optional[str] = None, cache_dir: Optional[str] = None, session_id: str = "default", enable_db: bool = True, max_history: int = 10, use_embeddings: bool = False, use_sqlite_tree: bool = False):
        """
        Initialize NaviDoc SDK.
        
        :param model: Ollama model name (default: 'qwen2.5:1.5b')
        :param cache_dir: Directory for storage (default: 'storage')
        :param session_id: Session ID for chat history
        :param enable_db: Whether to use SQLite for chat storage
        :param max_history: Maximum number of chat turns to keep in context
        :param use_embeddings: Whether to use fast embeddings for tree navigation
        :param use_sqlite_tree: Whether to store document tree in SQLite for large files
        """
        self.model = model or os.getenv("NAVIDOC_MODEL_NAME", "qwen2.5:1.5b")


        self.cache_dir = cache_dir or os.getenv("NAVIDOC_CACHE_DIR", "storage")
        self.session_id = session_id
        self.enable_db = enable_db
        self.max_history = max_history
        self.use_embeddings = use_embeddings
        self.use_sqlite_tree = use_sqlite_tree
        
        self.index = None
        self.index_type = None # "tree", "page", or "sqlite_tree"
        self.current_doc_id = None
        
        print(f"NaviDoc SDK initialized.")
        print(f"Model: {self.model}")
        print(f"Cache Dir: {self.cache_dir}")
        print(f"Session ID: {self.session_id}")
        print(f"History Limit: {self.max_history} turns")
        print(f"Use Embeddings: {self.use_embeddings}")
        print(f"Use SQLite Tree: {self.use_sqlite_tree}")
        
        # Initialize SQLite Database if enabled
        if self.enable_db:
            db_path = os.path.join(self.cache_dir, "navidoc.db")
            self.db = Database(db_path)
        else:
            self.db = None
            self.history: List[Dict[str, str]] = []
            
        # Initialize Embedding Model if requested
        self.embedding_model = None
        if self.use_embeddings:
            try:
                from model2vec import StaticModel
                print("Loading Model2Vec 'potion-base-32M' for super-fast navigation...")
                self.embedding_model = StaticModel.from_pretrained("minishlab/potion-base-32M")
                print("Model2Vec loaded successfully.")
            except ImportError:
                # Fallback to sentence-transformers
                try:
                    from sentence_transformers import SentenceTransformer
                    print("Loading Sentence Transformer model ('all-MiniLM-L6-v2') for navigation...")
                    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                    self.embedding_model.max_seq_length = 128
                    print("Sentence Transformer loaded successfully.")
                except ImportError:
                    print("Warning: Neither 'model2vec' nor 'sentence-transformers' installed. Falling back to LLM navigation.")
                    self.use_embeddings = False
        
        # Check Ollama status on init
        if self.is_ollama_running():
            print("Ollama service: Connected")
            self._ensure_model_exists()
        else:
            print("\nWarning: Could not connect to Ollama.")
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
            pulled_models = []
            for m in models_response.get('models', []):
                if isinstance(m, dict):
                    pulled_models.append(m.get('name') or m.get('model') or '')
                else:
                    pulled_models.append(getattr(m, 'model', '') or getattr(m, 'name', ''))
            
            found = False
            for m in pulled_models:
                if m == self.model or (isinstance(m, str) and m.startswith(self.model + ":")):
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

    def _save_tree_to_db(self, node: Dict[str, Any], doc_id: str, parent_id: Optional[int] = None):
        """Recursively save tree nodes to SQLite."""
        title = node.get("title", "")
        content = node.get("content", "")
        
        node_id = self.db.save_node(doc_id, title, content, parent_id)
        
        for child in node.get("children", []):
            self._save_tree_to_db(child, doc_id, node_id)

    def ingest(self, file_path: str) -> str:
        """Ingest a document and create the appropriate index."""
        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found."

        ext = os.path.splitext(file_path)[1].lower()
        self.current_doc_id = file_path
        
        # Auto-detect large files (> 10MB) to use SQLite tree
        file_size = os.path.getsize(file_path)
        use_sqlite = self.use_sqlite_tree or (file_size > 10 * 1024 * 1024)
        if file_size > 10 * 1024 * 1024 and not self.use_sqlite_tree:
            print(f"Notice: File is large ({file_size / 1024 / 1024:.2f} MB). Auto-enabling SQLite tree storage.")
        
        # Parse based on extension
        if ext == '.md':
            parser = MarkdownParser()
            tree_data = parser.parse(file_path)
        elif ext == '.pdf':
            parser = PdfParser()
            tree_data = parser.parse(file_path)
        elif ext == '.docx':
            parser = DocxParser()
            tree_data = parser.parse(file_path)
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
                try:
                    os.remove(temp_md_path)
                except:
                    pass
            except ImportError:
                return "Error: 'glmocr' is not installed. Please run `pip install glmocr` to enable image support."
            except Exception as e:
                return f"Error during OCR processing: {e}"
        else:
            return f"Unsupported file format: {ext}"

        # Handle Tree Data storage based on user choice
        if use_sqlite and self.db:
            print(f"Storing tree in SQLite for: {file_path}")
            self.db.clear_document(file_path) # Clear old if exists
            self._save_tree_to_db(tree_data, file_path)
            self.index_type = "sqlite_tree"
            return f"Successfully ingested {ext.upper()} (SQLite Tree): {file_path}"
        else:
            self.index = TreeIndex()
            self.index.load_tree(tree_data)
            self.index_type = "tree"
            return f"Successfully ingested {ext.upper()}: {file_path}"

    def _compress_text(self, text: str, max_sentences: int = 5) -> str:
        """Pure-Python extractive summarization based on word frequency."""
        import re
        from collections import Counter
        
        # Split into sentences
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
        if len(sentences) <= max_sentences:
            return text
            
        # Tokenize and score words
        words = re.findall(r'\b\w+\b', text.lower())
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'to', 'for', 'in', 'of', 'on', 'with', 'by', 'at', 'this', 'that'}
        
        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
        word_counts = Counter(filtered_words)
        
        if not word_counts:
            return " ".join(sentences[:max_sentences])
            
        sentence_scores = []
        for i, sent in enumerate(sentences):
            sent_words = re.findall(r'\b\w+\b', sent.lower())
            score = sum(word_counts[w] for w in sent_words if w in word_counts)
            sentence_scores.append((score, i, sent))
            
        top_sentences = sorted(sentence_scores, key=lambda x: x[0], reverse=True)[:max_sentences]
        top_sentences = sorted(top_sentences, key=lambda x: x[1])
        
        print(f"Compressed text from {len(sentences)} to {len(top_sentences)} sentences.")
        return " ".join([sent for _, _, sent in top_sentences])

    def save_index(self, file_name: str):
        """Save the current index to the cache directory (Only for JSON-based trees)."""
        if self.index_type == "sqlite_tree":
            print("Index is stored in SQLite database. No need to save to JSON.")
            return
            
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

    def _navigate_sqlite_tree(self, query: str, doc_id: str, parent_id: Optional[int]) -> str:
        """Navigate tree stored in SQLite."""
        children = self.db.get_children(doc_id, parent_id)
        
        if not children:
            if parent_id is not None:
                node = self.db.get_node(parent_id)
                content = node.get("content", "") if node else ""
                if self._verify_relevance(query, content):
                    return content
                else:
                    return "NOT_RELEVANT"
            return "No content."

        headers = [child["title"] for child in children]
        
        # Use Embeddings if enabled
        if self.use_embeddings and self.embedding_model:
            query_emb = np.array(self.embedding_model.encode([query]))
            header_embs = np.array(self.embedding_model.encode(headers))
            
            query_emb = query_emb / np.linalg.norm(query_emb, axis=1, keepdims=True)
            header_embs = header_embs / np.linalg.norm(header_embs, axis=1, keepdims=True)
            
            scores = np.dot(query_emb, header_embs.T)[0]
            best_idx = np.argmax(scores)
            chosen_header = headers[best_idx]
            chosen_id = children[best_idx]["id"]
            
            print(f"Embedding Navigation (SQLite) chose: {chosen_header}")
            
            result = self._navigate_sqlite_tree(query, doc_id, chosen_id)
            if result == "NOT_RELEVANT":
                if parent_id is not None:
                    node = self.db.get_node(parent_id)
                    return node.get("content", "") if node else ""
                return "Not found."
            return result
            
        # Fallback to LLM
        else:
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
                    if parent_id is not None:
                        node = self.db.get_node(parent_id)
                        return node.get("content", "") if node else ""
                    return "Not found."
                    
                for child in children:
                    if child["title"] == chosen_header:
                        result = self._navigate_sqlite_tree(query, doc_id, child["id"])
                        if result == "NOT_RELEVANT":
                            if parent_id is not None:
                                node = self.db.get_node(parent_id)
                                return node.get("content", "") if node else ""
                            return "Not found."
                        return result
                        
                return "Navigation path lost."
                
            except Exception as e:
                return f"Navigation error: {str(e)}"

    def _navigate_tree(self, query: str, node: Dict[str, Any]) -> str:
        """Recursively navigate the tree using the local LLM or Embeddings."""
        if self.use_embeddings and self.embedding_model:
            headers = [child["title"] for child in node["children"]]
            query_emb = np.array(self.embedding_model.encode([query]))
            header_embs = np.array(self.embedding_model.encode(headers))
            query_emb = query_emb / np.linalg.norm(query_emb, axis=1, keepdims=True)
            header_embs = header_embs / np.linalg.norm(header_embs, axis=1, keepdims=True)
            scores = np.dot(query_emb, header_embs.T)[0]
            best_idx = np.argmax(scores)
            chosen_header = headers[best_idx]
            print(f"Embedding Navigation chose: {chosen_header}")
            
            for child in node["children"]:
                if child["title"] == chosen_header:
                    result = self._navigate_tree(query, child)
                    if result == "NOT_RELEVANT":
                        return node.get("content", "Content not found.")
                    return result
            return node.get("content", "Navigation path lost.")
            
        if not node.get("children"):
            content = node.get("content", "")
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

        if self.index_type == "sqlite_tree":
            relevant_content = self._navigate_sqlite_tree(prompt, self.current_doc_id, None)
        elif self.index_type == "tree":
            relevant_content = self._navigate_tree(prompt, self.index.tree)
            if relevant_content == "NOT_RELEVANT":
                relevant_content = self.index.tree.get("content", "No relevant content found.")
        else:
            relevant_content = self.index.get_all_text()

        # Compress text if it is too long (e.g., > 3000 characters)
        if len(relevant_content) > 3000:
            relevant_content = self._compress_text(relevant_content)

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

        if self.index_type == "sqlite_tree":
            relevant_content = self._navigate_sqlite_tree(prompt, self.current_doc_id, None)
        elif self.index_type == "tree":
            relevant_content = self._navigate_tree(prompt, self.index.tree)
            if relevant_content == "NOT_RELEVANT":
                relevant_content = self.index.tree.get("content", "No relevant content found.")
        else:
            relevant_content = self.index.get_all_text()

        # Compress text if it is too long (e.g., > 3000 characters)
        if len(relevant_content) > 3000:
            relevant_content = self._compress_text(relevant_content)

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

    def get_documents(self) -> List[Dict[str, str]]:
        """Get list of available documents with name and id."""
        import os
        if self.db:
            docs = self.db.get_available_documents()
            return [{"name": os.path.basename(doc), "id": doc} for doc in docs]
        return []

