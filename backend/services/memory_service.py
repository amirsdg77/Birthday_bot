"""
Memory Service — persistent conversation history.
Uses PostgreSQL (via DATABASE_URL env var) in production on Render,
falls back to local SQLite for development.
"""

import os
import threading
from pathlib import Path

from sqlalchemy import create_engine
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

_store: dict[str, SQLChatMessageHistory] = {}
_lock = threading.Lock()
_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            # Supabase/PostgreSQL in production
            _engine = create_engine(database_url)
        else:
            # Local SQLite fallback for development
            db_dir = Path("/app/data")
            db_dir.mkdir(parents=True, exist_ok=True)
            _engine = create_engine(
                f"sqlite:///{db_dir / 'chat_history.db'}",
                connect_args={"check_same_thread": False},
            )
    return _engine


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    Returns the SQLite-backed chat history for a session.
    Safe to call from sync or threaded contexts (used by RunnableWithMessageHistory).
    """
    with _lock:
        if session_id not in _store:
            _store[session_id] = SQLChatMessageHistory(
                session_id=session_id,
                connection=_get_engine(),
            )
        return _store[session_id]


def clear_session(session_id: str) -> None:
    """Deletes all messages for a session from the DB and cache."""
    with _lock:
        history = _store.pop(session_id, None)
        if history:
            history.clear()
        else:
            SQLChatMessageHistory(
                session_id=session_id,
                connection=_get_engine(),
            ).clear()


def get_all_sessions() -> list[str]:
    """Returns all currently cached session IDs."""
    with _lock:
        return list(_store.keys())
