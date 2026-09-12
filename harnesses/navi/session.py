"""
Session management for Navi bot - tracks conversation history per user
"""
import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, db_path: str = None):
        """Initialize session manager with SQLite database"""
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'sessions.db')

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Sessions table - one per user
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                user_id INTEGER PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                last_activity TIMESTAMP NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        """)

        # Messages table - conversation history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES sessions(user_id)
            )
        """)

        # Index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_user_time
            ON messages(user_id, timestamp DESC)
        """)

        conn.commit()
        conn.close()
        logger.info(f"Session database initialized at {self.db_path}")

    def get_or_create_session(self, user_id: int, chat_id: int) -> Dict:
        """Get existing session or create new one"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if session exists
        cursor.execute("""
            SELECT user_id, chat_id, last_activity, created_at
            FROM sessions
            WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        now = datetime.now()

        if row:
            # Update last activity
            cursor.execute("""
                UPDATE sessions
                SET last_activity = ?
                WHERE user_id = ?
            """, (now, user_id))
            conn.commit()

            session = {
                'user_id': row[0],
                'chat_id': row[1],
                'last_activity': row[2],
                'created_at': row[3]
            }
        else:
            # Create new session
            cursor.execute("""
                INSERT INTO sessions (user_id, chat_id, last_activity, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, chat_id, now, now))
            conn.commit()

            session = {
                'user_id': user_id,
                'chat_id': chat_id,
                'last_activity': now,
                'created_at': now
            }
            logger.info(f"Created new session for user {user_id}")

        conn.close()
        return session

    def add_message(self, user_id: int, role: str, content: str):
        """Add message to conversation history"""
        if role not in ['user', 'assistant']:
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO messages (user_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, role, content, datetime.now()))

        conn.commit()
        conn.close()
        logger.debug(f"Added {role} message for user {user_id} ({len(content)} chars)")

    def get_context(self, user_id: int, max_messages: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT role, content, timestamp
            FROM messages
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, max_messages))

        rows = cursor.fetchall()
        conn.close()

        # Reverse to get chronological order (oldest first)
        messages = [
            {
                'role': row[0],
                'content': row[1],
                'timestamp': row[2]
            }
            for row in reversed(rows)
        ]

        logger.debug(f"Retrieved {len(messages)} messages for user {user_id}")
        return messages

    def clear_session(self, user_id: int):
        """Clear conversation history for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Delete messages
        cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))

        # Reset session timestamp
        cursor.execute("""
            UPDATE sessions
            SET last_activity = ?, created_at = ?
            WHERE user_id = ?
        """, (datetime.now(), datetime.now(), user_id))

        conn.commit()
        conn.close()
        logger.info(f"Cleared session for user {user_id}")

    def cleanup_expired_sessions(self, timeout_minutes: int = 30) -> int:
        """Remove messages from sessions that have been inactive"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = datetime.now() - timedelta(minutes=timeout_minutes)

        # Find expired sessions
        cursor.execute("""
            SELECT user_id FROM sessions
            WHERE last_activity < ?
        """, (cutoff,))

        expired_users = [row[0] for row in cursor.fetchall()]

        if expired_users:
            # Delete old messages
            placeholders = ','.join('?' * len(expired_users))
            cursor.execute(f"""
                DELETE FROM messages
                WHERE user_id IN ({placeholders})
            """, expired_users)

            deleted = cursor.rowcount
            conn.commit()
            logger.info(f"Cleaned up {deleted} messages from {len(expired_users)} expired sessions")
        else:
            deleted = 0

        conn.close()
        return deleted

    def get_session_stats(self, user_id: int) -> Dict:
        """Get statistics about user's session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
            FROM messages
            WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()

        cursor.execute("""
            SELECT created_at, last_activity
            FROM sessions
            WHERE user_id = ?
        """, (user_id,))

        session_row = cursor.fetchone()
        conn.close()

        if row and row[0] > 0:
            return {
                'message_count': row[0],
                'first_message': row[1],
                'last_message': row[2],
                'session_created': session_row[0] if session_row else None,
                'last_activity': session_row[1] if session_row else None
            }
        else:
            return {
                'message_count': 0,
                'first_message': None,
                'last_message': None,
                'session_created': session_row[0] if session_row else None,
                'last_activity': session_row[1] if session_row else None
            }

    def format_context_for_claude(self, messages: List[Dict[str, str]]) -> str:
        """Format conversation history for Claude prompt"""
        if not messages:
            return ""

        context_lines = ["Previous conversation:"]
        context_lines.append("-" * 40)

        for msg in messages:
            role_label = "You" if msg['role'] == 'user' else "Assistant"
            content = msg['content']

            # Truncate very long messages
            if len(content) > 500:
                content = content[:497] + "..."

            context_lines.append(f"{role_label}: {content}")

        context_lines.append("-" * 40)
        context_lines.append("\nCurrent message:")

        return "\n".join(context_lines)
