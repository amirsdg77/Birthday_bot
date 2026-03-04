"""
FastAPI entry point.
Endpoints:
  POST   /auth              — verify access password
  POST   /chat              — send a message, get full response
  GET    /chat/stream       — send a message, get SSE token stream
  GET    /greeting          — get an opening greeting
  GET    /history/{id}      — get past messages for a session
  POST   /prompts/reload    — hot-reload prompt .md files
  DELETE /session/{id}      — clear conversation history for a session
  GET    /health            — health check
"""

import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import settings
from services.chat_service import chat, chat_stream, get_greeting
from services.memory_service import clear_session, get_session_history
from services.prompt_service import reload_prompts, is_birthday

app = FastAPI(title="Bestie Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Request / Response models ----------

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None  # Auto-generated if not provided


class ChatResponse(BaseModel):
    reply: str
    session_id: str


class SimpleResponse(BaseModel):
    message: str


class GreetingResponse(BaseModel):
    message: str
    is_birthday: bool


class AuthRequest(BaseModel):
    password: str


class AuthResponse(BaseModel):
    ok: bool


class HistoryMessage(BaseModel):
    role: str   # "human" or "ai"
    text: str


# ---------- Routes ----------

@app.post("/auth", response_model=AuthResponse)
async def auth_endpoint(body: AuthRequest):
    """Verifies the access password. Returns ok=true on success."""
    if body.password == settings.ACCESS_PASSWORD:
        return AuthResponse(ok=True)
    raise HTTPException(status_code=401, detail="Wrong password 🔒")

@app.get("/history/{session_id}", response_model=list[HistoryMessage])
async def history_endpoint(session_id: str):
    """Returns all past messages for a session from SQLite."""
    history = get_session_history(session_id)
    result = []
    for msg in history.messages:
        role = "human" if msg.type == "human" else "ai"
        result.append(HistoryMessage(role=role, text=msg.content))
    return result


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(body: ChatRequest):
    session_id = body.session_id or str(uuid.uuid4())
    try:
        reply = await chat(body.message, session_id)
        return ChatResponse(reply=reply, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/stream")
async def chat_stream_endpoint(message: str, session_id: str | None = None):
    """
    SSE streaming endpoint — yields tokens as they arrive from Gemini.
    Each event: data: <chunk>\\n\\n
    Final event: data: [DONE]\\n\\n
    """
    sid = session_id or str(uuid.uuid4())

    async def event_generator():
        yield f"event: session\ndata: {sid}\n\n"
        try:
            async for chunk in chat_stream(message, sid):
                escaped = chunk.replace("\n", "\\n")
                yield f"data: {escaped}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/greeting", response_model=GreetingResponse)
async def greeting_endpoint(session_id: str):
    try:
        return GreetingResponse(message=await get_greeting(session_id), is_birthday=is_birthday())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prompts/reload", response_model=SimpleResponse)
async def reload_prompts_endpoint():
    """Hot-reload prompt .md files without restarting the server."""
    await reload_prompts()
    return SimpleResponse(message="Prompts reloaded from disk.")


@app.delete("/session/{session_id}", response_model=SimpleResponse)
async def clear_session_endpoint(session_id: str):
    clear_session(session_id)
    return SimpleResponse(message=f"Session {session_id} cleared.")


@app.get("/health")
async def health():
    return {"status": "ok"}
