"""
Memory Service — persistent conversation history via SQLite.
History survives container restarts and page refreshes.
The DB file lives at /app/data/chat_history.db (mounted as a Docker volume).

Uses a single shared SQLAlchemy engine with check_same_thread=False so
the sync get_session_history() can be called from LangChain's thread pool
without SQLite complaints.
"""

import threading
from pathlib import Path

from sqlalchemy import create_engine
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

DB_DIR = Path("/app/data")
DB_PATH = DB_DIR / "chat_history.db"

_store: dict[str, SQLChatMessageHistory] = {}
_lock = threading.Lock()
_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            f"sqlite:///{DB_PATH}",
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
