import sqlite3
import os
from typing import List, Dict

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
