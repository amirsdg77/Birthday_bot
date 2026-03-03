"""
Prompt Service — loads prompt templates from /prompts/*.md files.
To edit a prompt, just edit the corresponding markdown file — no code changes needed.

Date/time is injected automatically into every system prompt so the bot
is always aware of the current moment (and Orgese's birthday on March 5).
"""

import asyncio
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import aiofiles
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# TODO: Change this to Orgese's timezone if needed
# Full list: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIMEZONE = ZoneInfo("Europe/Istanbul")

BIRTHDAY_MONTH = 3
BIRTHDAY_DAY = 5

# In-memory cache: prompt name → raw string content
_prompt_cache: dict[str, str] = {}
_cache_lock = asyncio.Lock()


def _now() -> datetime:
    return datetime.now(tz=TIMEZONE)


def _date_context() -> str:
    """Returns a short date/time string injected into every system prompt."""
    now = _now()
    return (
        f"\n\n---\n"
        f"Current date: {now.strftime('%A, %B %d, %Y')}\n"
        f"Current time: {now.strftime('%H:%M')} ({TIMEZONE.key})\n"
        f"---"
    )


def is_birthday() -> bool:
    """Returns True if today is March 5th (Orgese's birthday)."""
    now = _now()
    return now.month == BIRTHDAY_MONTH and now.day == BIRTHDAY_DAY


async def _load_prompt_file(name: str) -> str:
    """Reads a markdown prompt file from disk asynchronously."""
    path = PROMPTS_DIR / f"{name}.md"
    async with aiofiles.open(path, mode="r", encoding="utf-8") as f:
        return await f.read()


async def get_prompt_text(name: str) -> str:
    """
    Returns the raw text of a prompt file.
    Reads from disk once per process lifetime, then serves from cache.
    Thread-safe via asyncio.Lock.
    """
    async with _cache_lock:
        if name not in _prompt_cache:
            _prompt_cache[name] = await _load_prompt_file(name)
        return _prompt_cache[name]


async def reload_prompts() -> None:
    """
    Clears the prompt cache so .md files are re-read on next request.
    Useful in dev when you edit a prompt file and want changes applied instantly.
    """
    async with _cache_lock:
        _prompt_cache.clear()


async def get_chat_prompt() -> ChatPromptTemplate:
    """
    Main conversational prompt: system message + date context + history + user input.
    Birthday prompt is only used for the one-time greeting — chat always uses system.md.
    """
    system_text = await get_prompt_text("system")
    system_text += _date_context()

    return ChatPromptTemplate.from_messages([
        ("system", system_text),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])


async def get_greeting_prompt() -> ChatPromptTemplate:
    """
    Opening greeting prompt used on app load.
    On her birthday, uses birthday.md instead of greeting.md.
    """
    if is_birthday():
        system_text = await get_prompt_text("birthday")
    else:
        system_text = await get_prompt_text("greeting")
    system_text += _date_context()

    human_text = (
        "Send bestie her special birthday message — it's her birthday today! 🎂"
        if is_birthday()
        else "Greet bestie as she opens the app."
    )

    return ChatPromptTemplate.from_messages([
        ("system", system_text),
        ("human", human_text),
    ])
