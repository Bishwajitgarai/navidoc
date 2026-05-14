import sqlite3
import os
from typing import List, Dict, Any, Optional

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database and create tables if they don't exist."""
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create chat history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_msg TEXT,
                assistant_msg TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create document nodes table for large PDF/Doc trees (Adjacency List Model)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id TEXT,
                title TEXT,
                content TEXT,
                parent_id INTEGER,
                FOREIGN KEY (parent_id) REFERENCES document_nodes(id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def save_chat(self, session_id: str, user_msg: str, assistant_msg: str):
        """Save a chat turn to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chat_history (session_id, user_msg, assistant_msg)
            VALUES (?, ?, ?)
        ''', (session_id, user_msg, assistant_msg))
        conn.commit()
        conn.close()

    def load_chat(self, session_id: str) -> List[Dict[str, str]]:
        """Load chat history for a session from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_msg, assistant_msg FROM chat_history
            WHERE session_id = ?
            ORDER BY timestamp ASC
        ''', (session_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [{"user": row[0], "assistant": row[1]} for row in rows]

    def clear_chat(self, session_id: str):
        """Clear chat history for a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM chat_history WHERE session_id = ?
        ''', (session_id,))
        conn.commit()
        conn.close()

    # --- New Methods for SQLite-based Tree ---
    
    def save_node(self, doc_id: str, title: str, content: str, parent_id: Optional[int] = None) -> int:
        """Save a tree node and return its ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO document_nodes (doc_id, title, content, parent_id)
            VALUES (?, ?, ?, ?)
        ''', (doc_id, title, content, parent_id))
        node_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return node_id

    def get_children(self, doc_id: str, parent_id: Optional[int]) -> List[Dict[str, Any]]:
        """Get children of a specific node."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if parent_id is None:
            cursor.execute('''
                SELECT id, title, content FROM document_nodes
                WHERE doc_id = ? AND parent_id IS NULL
            ''', (doc_id,))
        else:
            cursor.execute('''
                SELECT id, title, content FROM document_nodes
                WHERE doc_id = ? AND parent_id = ?
            ''', (doc_id, parent_id))
        rows = cursor.fetchall()
        conn.close()
        return [{"id": row[0], "title": row[1], "content": row[2]} for row in rows]

    def get_node(self, node_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific node by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, content, parent_id FROM document_nodes
            WHERE id = ?
        ''', (node_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {"id": row[0], "title": row[1], "content": row[2], "parent_id": row[3]}
        return None

    def clear_document(self, doc_id: str):
        """Clear all nodes for a specific document."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM document_nodes WHERE doc_id = ?
        ''', (doc_id,))
        conn.commit()
        conn.close()

    def get_available_documents(self) -> List[str]:
        """Get list of distinct document IDs stored in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT doc_id FROM document_nodes
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]

