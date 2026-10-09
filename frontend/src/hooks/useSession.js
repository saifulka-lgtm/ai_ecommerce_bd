import { useState } from "react";

const KEY = "ai_ecommerce_session_id";

function generateId() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID();
  return `sess-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function useSession() {
  const [sessionId] = useState(() => {
    let id = localStorage.getItem(KEY);
    if (!id) {
      id = generateId();
      localStorage.setItem(KEY, id);
    }
    return id;
  });
  return sessionId;
}
