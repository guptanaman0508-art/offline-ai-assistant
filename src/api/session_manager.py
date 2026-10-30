"""
Session and in-memory conversation history management for local offline assistant.

Note on session persistence:
This in-memory session manager holds multi-turn conversation histories in memory
isolated by session ID. When the backend application process restarts, in-memory sessions
are cleared. No persistent database or cloud storage is used.
"""

import uuid
from typing import Dict, List, Optional


SYSTEM_PROMPT = (
    "You are a helpful, accurate, and concise offline study and notes assistant. "
    "Provide clear explanations and structured answers."
)


class SessionManager:
    """Manages in-memory conversation histories partitioned by session ID."""

    def __init__(self, system_prompt: str = SYSTEM_PROMPT):
        self._system_prompt = system_prompt
        # Maps session_id (str) -> List[Dict[str, str]] (messages: [{"role": ..., "content": ...}])
        self._sessions: Dict[str, List[Dict[str, str]]] = {}

    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """
        Validate an existing session ID or generate a new unique session ID.
        """
        if not session_id or not session_id.strip():
            session_id = str(uuid.uuid4())
        
        if session_id not in self._sessions:
            self._sessions[session_id] = [
                {"role": "system", "content": self._system_prompt}
            ]
        return session_id

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Return the conversation message history for a given session ID."""
        if session_id not in self._sessions:
            self.get_or_create_session(session_id)
        # Return a shallow copy of message dicts to avoid external corruption
        return list(self._sessions[session_id])

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Append a user or assistant message to the session's conversation history."""
        if session_id not in self._sessions:
            self.get_or_create_session(session_id)
        self._sessions[session_id].append({"role": role, "content": content})

    def clear_history(self, session_id: Optional[str] = None) -> bool:
        """
        Clear conversation history.
        If session_id is provided, reset only that session's history back to system prompt.
        If session_id is None, reset all active sessions.
        Returns True if history was cleared.
        """
        if session_id is not None:
            if session_id in self._sessions:
                self._sessions[session_id] = [
                    {"role": "system", "content": self._system_prompt}
                ]
                return True
            return False
        
        # Clear all sessions
        self._sessions.clear()
        return True

    def list_active_sessions(self) -> List[str]:
        """Return list of active session IDs in memory."""
        return list(self._sessions.keys())
