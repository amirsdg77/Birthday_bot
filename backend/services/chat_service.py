"""
Chat Service — async orchestrator for LLM + memory + prompts.
All public functions are async and safe to call concurrently.

History is managed manually (not via RunnableWithMessageHistory) so we
can use a plain sync SQLite engine without async/sync conflicts.
"""

from typing import AsyncIterator

from langchain_core.messages import HumanMessage, AIMessage

from services.llm_service import get_llm
from services.memory_service import get_session_history
from services.prompt_service import get_chat_prompt, get_greeting_prompt


async def chat(user_message: str, session_id: str) -> str:
    """
    Sends a user message and returns the complete AI reply.
    Reads and writes history manually to avoid async/sync conflicts.
    """
    history = get_session_history(session_id)
    prompt = await get_chat_prompt()
    llm = get_llm()

    formatted = await prompt.ainvoke({"input": user_message, "history": history.messages})
    response = await llm.ainvoke(formatted.to_messages())

    # Persist both sides to SQLite
    history.add_message(HumanMessage(content=user_message))
    history.add_message(AIMessage(content=response.content))

    return response.content


async def chat_stream(user_message: str, session_id: str) -> AsyncIterator[str]:
    """
    Streams the AI reply token by token.
    Yields plain text chunks — the caller wraps them in SSE.
    Saves the full exchange to SQLite after the stream completes.
    """
    history = get_session_history(session_id)
    prompt = await get_chat_prompt()
    llm = get_llm()

    formatted = await prompt.ainvoke({"input": user_message, "history": history.messages})

    full_reply = []
    async for chunk in llm.astream(formatted.to_messages()):
        if chunk.content:
            full_reply.append(chunk.content)
            yield chunk.content

    # Persist the full exchange once streaming is done
    history.add_message(HumanMessage(content=user_message))
    history.add_message(AIMessage(content="".join(full_reply)))


async def get_greeting() -> str:
    """Generates an opening greeting when bestie first opens the app."""
    prompt = await get_greeting_prompt()
    chain = prompt | get_llm()
    response = await chain.ainvoke({})
    return response.content
