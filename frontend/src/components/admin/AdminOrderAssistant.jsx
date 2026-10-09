import React, { useState, useRef, useEffect } from "react";
import { api } from "../../services/api";

const EXAMPLES = ["কনফার্মড অর্ডার দেখাও", "DEMO-1234 শিপ করো", "DEMO-1234 ডেলিভার্ড করো"];

export default function AdminOrderAssistant({ token, onChanged }) {
  const [messages, setMessages] = useState([
    { role: "ai", text: "অর্ডার নম্বর আর কী করতে হবে লিখুন — যেমন \"DEMO-1234 শিপ করো\"।" },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text) => {
    const message = (text ?? input).trim();
    if (!message || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: message }]);
    setBusy(true);
    try {
      const res = await api.adminAiChat(token, message);
      setMessages((m) => [...m, { role: "ai", text: res.reply }]);
      if (res.changed) onChanged?.();
    } catch (err) {
      setMessages((m) => [...m, { role: "ai", text: `ত্রুটি: ${err.message}` }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 12, padding: 14, marginBottom: 18 }}>
      <div style={{ fontWeight: 800, fontSize: 13, marginBottom: 8 }}>AI Order Assistant</div>

      <div style={{ maxHeight: 180, overflowY: "auto", display: "flex", flexDirection: "column", gap: 6, marginBottom: 10 }}>
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              alignSelf: m.role === "user" ? "flex-end" : "flex-start",
              background: m.role === "user" ? "var(--bd-green-light)" : "var(--bg-3)",
              color: m.role === "user" ? "#08130d" : "var(--text-0)",
              borderRadius: 10,
              padding: "6px 10px",
              fontSize: 12,
              whiteSpace: "pre-line",
              maxWidth: "85%",
            }}
          >
            {m.text}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 8 }}>
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => send(ex)}
            disabled={busy}
            style={{ background: "var(--bg-3)", border: "1px solid var(--border)", color: "var(--text-1)", borderRadius: 999, padding: "3px 10px", fontSize: 11, cursor: "pointer" }}
          >
            {ex}
          </button>
        ))}
      </div>

      <form onSubmit={(e) => { e.preventDefault(); send(); }} style={{ display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="যেমন: DEMO-1234 ডেলিভার্ড করো"
          style={{ flex: 1, background: "var(--bg-3)", border: "1px solid var(--border)", color: "var(--text-0)", borderRadius: 8, padding: "8px 10px", fontSize: 12 }}
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          style={{ background: "var(--bd-green-light)", color: "#08130d", border: "none", borderRadius: 8, padding: "0 16px", fontWeight: 700, fontSize: 12, cursor: "pointer" }}
        >
          {busy ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}
