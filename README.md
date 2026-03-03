# Bestie Chatbot

A personal AI chatbot built as a gift. Powered by Google Gemini, with persistent memory, streaming responses, and a special birthday surprise.

---

## Stack

| Layer    | Tech                              |
|----------|-----------------------------------|
| Frontend | React                             |
| Backend  | FastAPI (Python)                  |
| LLM      | Google Gemini via LangChain       |
| Memory   | SQLite (persistent across restarts) |
| Infra    | Docker Compose                    |

---

## Setup

### 1. Fill in `.env`

```env
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-2.5-flash
TEMPERATURE=0.8
MAX_TOKENS=1024
ACCESS_PASSWORD=your_password_here
```

### 2. Run

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

---

## Features

- **Password gate** — only the right person gets in
- **Streaming responses** — tokens appear as they're generated
- **Persistent memory** — chat history survives refreshes and restarts
- **Birthday mode** — on March 5th, the bot opens with a special birthday message
- **Markdown prompts** — edit `backend/prompts/*.md` to change personality without touching code
- **Hot-reload prompts** — `POST /prompts/reload` applies prompt edits instantly without restart

---

## Prompts

| File          | Purpose                                      |
|---------------|----------------------------------------------|
| `system.md`   | Core personality, tone, and characteristics  |
| `greeting.md` | Opening message when the app is first loaded |
| `birthday.md` | Birthday greeting (used once on March 5th)   |

---

## Useful Commands

```bash
# View logs
docker compose logs -f

# Clear chat history (wipe database)
docker exec bbyproject-backend-1 rm -f /app/data/chat_history.db

# Hot-reload prompts after editing .md files
curl -X POST http://localhost:8000/prompts/reload

# Health check
curl http://localhost:8000/health
```

---

## After Birthday Testing

Remember to change `BIRTHDAY_DAY` back to `5` in [backend/services/prompt_service.py](backend/services/prompt_service.py#L24).
