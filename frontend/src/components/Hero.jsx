import React from "react";

export default function Hero({ onAskAI }) {
  return (
    <section
      style={{
        padding: "64px 28px 40px",
        textAlign: "center",
        background:
          "radial-gradient(ellipse at center top, rgba(0,106,78,0.25), transparent 60%)",
      }}
    >
      <h1 style={{ fontSize: "clamp(28px, 5vw, 46px)", fontWeight: 800, margin: "0 0 14px", lineHeight: 1.15 }}>
        Everyday fashion,
        <br />
        <span style={{ color: "var(--bd-green-light)" }}>made effortless with AI.</span>
      </h1>
      <p style={{ maxWidth: 560, margin: "0 auto 28px", color: "var(--text-1)", fontSize: 16, lineHeight: 1.6 }}>
        Search in Bangla or English, check real price &amp; stock, build your cart,
        and check out — all through one conversation with our AI shopping assistant.
      </p>
      <button
        className="btn-primary"
        onClick={onAskAI}
        style={{ padding: "14px 28px", borderRadius: 999, fontSize: 15, fontWeight: 700 }}
      >
        ✨ Ask our AI Shopping Assistant
      </button>
    </section>
  );
}
