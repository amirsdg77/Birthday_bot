/**
 * API Service — all backend calls go through here.
 * Change REACT_APP_API_URL in .env to point to your backend.
 */

import axios from "axios";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL: BASE_URL });

/**
 * Streaming chat via SSE.
 * Calls onChunk(text) for each token, onDone(sessionId) when finished.
 * Returns an abort function to cancel mid-stream.
 */
export const streamMessage = (message, sessionId, { onChunk, onDone, onError }) => {
  const params = new URLSearchParams({ message });
  if (sessionId) params.set("session_id", sessionId);

  const url = `${BASE_URL}/chat/stream?${params.toString()}`;
  const es = new EventSource(url);
  let resolvedSessionId = sessionId;
  // Track whether we finished cleanly so we don't treat the post-close
  // reconnect attempt as an error (EventSource fires onerror on close too)
  let done = false;

  es.addEventListener("session", (e) => {
    resolvedSessionId = e.data;
  });

  es.onmessage = (e) => {
    if (e.data === "[DONE]") {
      done = true;
      es.close();
      onDone(resolvedSessionId);
      return;
    }
    // Unescape newlines that were escaped server-side
    onChunk(e.data.replace(/\\n/g, "\n"));
  };

  es.addEventListener("error", (e) => {
    if (done) return; // normal close after [DONE] — ignore
    es.close();
    onError?.(e.data || "Stream error");
  });

  // Return abort handle so the caller can cancel early
  return () => { done = true; es.close(); };
};

export const fetchGreeting = async () => {
  const res = await api.get("/greeting");
  return { message: res.data.message, isBirthday: res.data.is_birthday };
};

export const clearSession = async (sessionId) => {
  await api.delete(`/session/${sessionId}`);
};

export const verifyPassword = async (password) => {
  const res = await api.post("/auth", { password });
  return res.data.ok; // true if correct
};

/** Returns past messages as [{ role: "human"|"ai", text: string }] */
export const fetchHistory = async (sessionId) => {
  const res = await api.get(`/history/${sessionId}`);
  return res.data;
};
