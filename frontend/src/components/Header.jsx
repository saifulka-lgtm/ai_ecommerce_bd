import React from "react";
import { Link } from "react-router-dom";

export default function Header({ cartCount, onCartClick, onChatClick }) {
  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 40,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "16px 28px",
        background: "rgba(10, 15, 13, 0.85)",
        backdropFilter: "blur(10px)",
        borderBottom: "1px solid var(--border)",
      }}
    >
      <Link to="/" style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div
          style={{
            width: 38,
            height: 38,
            borderRadius: 10,
            background: "linear-gradient(135deg, var(--bd-green), var(--bd-red))",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 800,
            fontSize: 18,
          }}
        >
          FB
        </div>
        <div>
          <div style={{ fontWeight: 800, fontSize: 18, letterSpacing: 0.2 }}>Fashion BD</div>
        </div>
      </Link>

      <nav style={{ display: "flex", alignItems: "center", gap: 18 }}>
        <button
          onClick={onChatClick}
          style={{
            background: "none",
            border: "1px solid var(--border)",
            color: "var(--text-0)",
            padding: "8px 14px",
            borderRadius: 999,
            fontSize: 14,
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          💬 AI Assistant
        </button>
        <button
          onClick={onCartClick}
          style={{
            position: "relative",
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            color: "var(--text-0)",
            width: 40,
            height: 40,
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 18,
          }}
          aria-label="Cart"
        >
          🛒
          {cartCount > 0 && (
            <span
              style={{
                position: "absolute",
                top: -4,
                right: -4,
                background: "var(--bd-red)",
                color: "white",
                fontSize: 11,
                fontWeight: 700,
                borderRadius: 999,
                minWidth: 18,
                height: 18,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "0 4px",
              }}
            >
              {cartCount}
            </span>
          )}
        </button>
        <Link
          to="/admin"
          style={{ fontSize: 13, color: "var(--text-2)", border: "1px solid var(--border)", padding: "8px 12px", borderRadius: 999 }}
        >
          Admin
        </Link>
      </nav>
    </header>
  );
}
