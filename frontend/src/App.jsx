import { useState, useEffect, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import { streamMessage, fetchGreeting, clearSession, verifyPassword, fetchHistory } from "./api";
import avatar from "./avatar.jpg";
import BirthdayEffects from "./BirthdayEffects";
import "./App.css";

// Fixed session ID — stored in localStorage so it survives page refreshes
const STORAGE_KEY = "bestie_session_id";
const AUTH_KEY = "bestie_authed";

function getOrCreateSessionId() {
  let sid = localStorage.getItem(STORAGE_KEY);
  if (!sid) {
    sid = uuidv4();
    localStorage.setItem(STORAGE_KEY, sid);
  }
  return sid;
}

// ─── Lock Screen ────────────────────────────────────────────────────────────

function LockScreen({ onUnlock }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const ok = await verifyPassword(password);
      if (ok) {
        localStorage.setItem(AUTH_KEY, "1");
        onUnlock();
      } else {
        setError("Wrong password 🔒 Try again!");
      }
    } catch {
      setError("Something went wrong. Try again?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="lock-screen">
      <div className="lock-card">
        <div className="lock-icon">🌸</div>
        <h1 className="lock-title">hey bestie 💕</h1>
        <p className="lock-subtitle">enter your password to open our space</p>
        <form onSubmit={handleSubmit} className="lock-form">
          <input
            type="password"
            className="lock-input"
            placeholder="password..."
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
          />
          {error && <p className="lock-error">{error}</p>}
          <button type="submit" className="lock-btn" disabled={loading || !password}>
            {loading ? "checking..." : "come in 🌷"}
          </button>
        </form>
      </div>
    </div>
  );
}

// ─── Main Chat ───────────────────────────────────────────────────────────────

function Chat({ sessionId, onBirthday }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const bottomRef = useRef(null);
  const abortRef = useRef(null);

  useEffect(() => {
    const loadInitial = async () => {
      setIsStreaming(true);
      try {
        const history = await fetchHistory(sessionId);
        if (history.length > 0) {
          // Restore past bubbles — no greeting needed, she's been here before
          setMessages(
            history.map((m) => ({
              sender: m.role === "human" ? "user" : "bot",
              text: m.text,
              chunks: null,
              id: uuidv4(),
            }))
          );
        } else {
          // First ever visit — show a greeting
          const { message, isBirthday: bday } = await fetchGreeting(sessionId);
          appendMessage("bot", message);
          if (bday) onBirthday();
        }
      } catch {
        appendMessage("bot", "Hey bestie! 💕 So happy you're here!");
      } finally {
        setIsStreaming(false);
      }
    };
    loadInitial();
  }, [sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  const appendMessage = (sender, text) => {
    setMessages((prev) => [...prev, { sender, text, chunks: null, id: uuidv4() }]);
  };

  const startBotBubble = () => {
    const id = uuidv4();
    setMessages((prev) => [...prev, { sender: "bot", text: null, chunks: [], id }]);
    return id;
  };

  const appendChunk = (bubbleId, chunk) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === bubbleId ? { ...m, chunks: [...m.chunks, chunk] } : m
      )
    );
  };

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;

    appendMessage("user", trimmed);
    setInput("");
    setIsStreaming(true);

    const bubbleId = startBotBubble();

    abortRef.current = streamMessage(trimmed, sessionId, {
      onChunk: (chunk) => appendChunk(bubbleId, chunk),
      onDone: () => {
        setIsStreaming(false);
        abortRef.current = null;
      },
      onError: () => {
        appendChunk(bubbleId, "Oops, something went wrong bestie 😅");
        setIsStreaming(false);
        abortRef.current = null;
      },
    });
  };

  const handleClear = async () => {
    abortRef.current?.();
    await clearSession(sessionId);
    setMessages([]);
    appendMessage("bot", "Fresh start! What's on your mind, bestie? 🌸");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const lastBotId = messages.filter((m) => m.sender === "bot").at(-1)?.id;

  return (
    <div className="chat-wrapper">
      <div className="chat-header">
        <img src={avatar} alt="bestie" className="avatar" />
        <div className="info">
          <h2>starberry 🍓</h2>
          <span>always here for you</span>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.sender}`}>
            {msg.sender === "bot" && <img src={avatar} alt="" className="msg-avatar" />}
            <div className="bubble">
              {msg.chunks !== null
                ? msg.chunks.map((chunk, i) => (
                    <span key={i} className="token">{chunk}</span>
                  ))
                : msg.text?.split("\n").map((line, i, arr) => (
                    <span key={i}>{line}{i < arr.length - 1 && <br />}</span>
                  ))}
              {isStreaming && msg.id === lastBotId && (
                <span className="cursor" />
              )}
            </div>
          </div>
        ))}

        {isStreaming && messages.at(-1)?.sender !== "bot" && (
          <div className="message bot">
            <img src={avatar} alt="" className="msg-avatar" />
            <div className="typing-indicator">
              <span /><span /><span />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="chat-input-area">
        <input
          type="text"
          placeholder="Say something, bestie... 💬"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button className="send-btn" onClick={handleSend} disabled={isStreaming || !input.trim()}>
          ➤
        </button>
      </div>
    </div>
  );
}

// ─── Root ────────────────────────────────────────────────────────────────────

export default function App() {
  // Check localStorage so she stays logged in after page refresh
  const [authed, setAuthed] = useState(() => localStorage.getItem(AUTH_KEY) === "1");
  const [sessionId] = useState(getOrCreateSessionId);
  const [isBirthday, setIsBirthday] = useState(false);

  return (
    <>
      {isBirthday && <BirthdayEffects />}
      {authed
        ? <Chat sessionId={sessionId} onBirthday={() => setIsBirthday(true)} />
        : <LockScreen onUnlock={() => setAuthed(true)} />}
    </>
  );
}
