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

## Deploying to Render

The repo includes a `render.yaml` that sets up everything automatically.

### Steps

1. Push the project to a GitHub repo
2. Go to [render.com](https://render.com) → New → Blueprint → connect your repo
3. Render will detect `render.yaml` and create all three services automatically
4. Set the following environment variables manually in the Render dashboard (marked `sync: false`):

| Service | Variable | Value |
|---|---|---|
| bestie-backend | `GOOGLE_API_KEY` | your Google API key |
| bestie-backend | `ACCESS_PASSWORD` | the password you want |
| bestie-frontend | `REACT_APP_API_URL` | `https://bestie-backend.onrender.com` |
| bestie-keepalive | `BACKEND_URL` | `https://bestie-backend.onrender.com` |

5. Click **Deploy** — done!

### What gets created
- **bestie-backend** — FastAPI web service with a 1GB persistent disk for SQLite
- **bestie-frontend** — React static site
- **bestie-keepalive** — Cron job that pings `/health` every 10 minutes to keep the backend warm

---

## After Birthday Testing

Remember to change `BIRTHDAY_DAY` back to `5` in [backend/services/prompt_service.py](backend/services/prompt_service.py#L24).
