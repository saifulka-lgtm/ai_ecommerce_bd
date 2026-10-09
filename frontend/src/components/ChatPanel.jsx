import React, { useEffect, useRef, useState } from "react";
import { api } from "../services/api";
import ProductCard from "./ProductCard";

const SUGGESTED_PROMPTS = [
  "Show me men's T-shirts",
  "Show products under ৳1000",
  "Show black shirts",
  "কালো টি-শার্ট দেখাও",
  "Show my cart",
  "I want to place an order",
];

export default function ChatPanel({ sessionId, onAddToCart, onOpenCart, open, onOpen, onClose }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "হ্যালো! আমি আপনার AI শপিং অ্যাসিস্ট্যান্ট। Ask me anything — in Bangla or English — about our products, your cart, or your orders.",
      data: null,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  const send = async (text) => {
    const message = (text ?? input).trim();
    if (!message || loading) return;
    setMessages((m) => [...m, { role: "user", text: message, data: null }]);
    setInput("");
    setLoading(true);
    try {
      const res = await api.sendChatMessage(sessionId, message);
      setMessages((m) => [...m, { role: "assistant", text: res.reply, data: res.data, tool: res.tool_used }]);
      if (res.tool_used && ["add_to_cart", "remove_from_cart", "update_cart_quantity", "create_demo_order"].includes(res.tool_used)) {
        onOpenCart?.(false); // just trigger a silent cart refresh upstream
      }
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", text: `Sorry, something went wrong: ${e.message}`, data: null }]);
    } finally {
      setLoading(false);
    }
  };

  // Closed state: a small round floating button in the bottom-right corner,
  // Messenger-style — click to open the chat panel over the page.
  if (!open) {
    return (
      <button
        onClick={onOpen}
        aria-label="Open AI Shopping Assistant"
        style={{
          position: "fixed",
          bottom: 24,
          right: 24,
          zIndex: 55,
          width: 60,
          height: 60,
          borderRadius: "50%",
          border: "none",
          background: "linear-gradient(135deg, var(--bd-green), var(--bd-green-light))",
          boxShadow: "0 8px 24px rgba(0,106,78,0.45)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
        }}
      >
        <ChatIcon size={26} color="white" />
      </button>
    );
  }

  return (
    <section
      id="ai-assistant"
      style={{
        position: "fixed",
        bottom: 24,
        right: 24,
        zIndex: 55,
        width: "min(380px, calc(100vw - 32px))",
        height: "min(600px, calc(100vh - 48px))",
        background: "var(--bg-1)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        boxShadow: "0 16px 48px rgba(0,0,0,0.45)",
      }}
    >
      <div style={{ padding: "14px 16px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--success)", flexShrink: 0 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 800, fontSize: 14 }}>AI Shopping Assistant</div>
          <div style={{ fontSize: 11, color: "var(--text-2)" }}>Understands Bangla &amp; English · Uses real store data only</div>
        </div>
        <button
          onClick={onClose}
          aria-label="Close"
          style={{
            width: 30,
            height: 30,
            borderRadius: "50%",
            border: "1px solid var(--border)",
            background: "var(--bg-2)",
            color: "var(--text-1)",
            fontSize: 16,
            lineHeight: 1,
            cursor: "pointer",
            flexShrink: 0,
          }}
        >
          ×
        </button>
      </div>

      <div ref={scrollRef} style={{ flex: 1, overflowY: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 16 }}>
        {messages.map((m, i) => (
          <ChatBubble key={i} message={m} onAddToCart={onAddToCart} />
        ))}
        {loading && (
          <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--text-2)", fontSize: 13 }}>
            <span className="spinner" /> thinking…
          </div>
        )}
      </div>

      <div style={{ padding: "10px 14px", borderTop: "1px solid var(--border)" }}>
        <div style={{ display: "flex", gap: 8, overflowX: "auto", paddingBottom: 10 }}>
          {SUGGESTED_PROMPTS.map((p) => (
            <button
              key={p}
              onClick={() => send(p)}
              style={{
                whiteSpace: "nowrap",
                fontSize: 12,
                padding: "6px 12px",
                borderRadius: 999,
                border: "1px solid var(--border)",
                background: "var(--bg-2)",
                color: "var(--text-1)",
              }}
            >
              {p}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
          style={{ display: "flex", gap: 8 }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="বাংলা বা English-এ লিখুন…"
            style={{
              flex: 1,
              minWidth: 0,
              background: "var(--bg-2)",
              border: "1px solid var(--border)",
              color: "var(--text-0)",
              borderRadius: 999,
              padding: "12px 16px",
              fontSize: 14,
            }}
          />
          <button className="btn-primary" disabled={loading} style={{ borderRadius: 999, padding: "0 18px", fontSize: 14, fontWeight: 700, flexShrink: 0 }}>
            Send
          </button>
        </form>
      </div>
    </section>
  );
}

function ChatIcon({ size = 24, color = "currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M4 12c0-4.418 3.582-8 8-8s8 3.582 8 8-3.582 8-8 8c-1.13 0-2.204-.235-3.178-.658L4 20l1.05-4.202C4.384 14.68 4 13.383 4 12z"
        stroke={color}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ChatBubble({ message, onAddToCart }) {
  const isUser = message.role === "user";
  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start" }}>
      <div style={{ maxWidth: "85%", display: "flex", flexDirection: "column", gap: 10 }}>
        <div
          style={{
            background: isUser ? "linear-gradient(135deg, var(--bd-green), var(--bd-green-light))" : "var(--bg-2)",
            border: isUser ? "none" : "1px solid var(--border)",
            color: isUser ? "white" : "var(--text-0)",
            padding: "10px 14px",
            borderRadius: 14,
            borderBottomRightRadius: isUser ? 2 : 14,
            borderBottomLeftRadius: isUser ? 14 : 2,
            fontSize: 14,
            lineHeight: 1.5,
            whiteSpace: "pre-line",
          }}
        >
          {message.text}
        </div>

        {message.data?.products?.length > 0 && (
          <div style={{ display: "flex", gap: 10, overflowX: "auto", paddingBottom: 4 }}>
            {message.data.products.map((p) => (
              <ProductCard key={p.id} product={p} compact onAddToCart={onAddToCart} />
            ))}
          </div>
        )}

        {message.data?.order && <OrderCard order={message.data.order} />}

        {message.data?.items && Array.isArray(message.data.items) && (
          <CartMiniSummary data={message.data} />
        )}

        {message.data?.orders?.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {message.data.orders.map((o) => (
              <OrderCard key={o.order_number} order={o} compact />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function OrderCard({ order, compact }) {
  const rows = { color: "var(--text-2)", display: "flex", justifyContent: "space-between", gap: 12 };
  const strong = { color: "var(--text-0)" };
  const showDetails = !compact && Array.isArray(order.items) && order.items.length > 0;
  return (
    <div style={{ background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 10, padding: 12, fontSize: 12, minWidth: 220 }}>
      <div style={{ fontWeight: 800, marginBottom: 4 }}>{order.order_number}</div>
      <div style={{ color: "var(--text-2)" }}>Status: <b style={strong}>{order.order_status}</b></div>
      <div style={{ color: "var(--text-2)" }}>Payment: <b style={strong}>{order.payment_status}</b></div>

      {showDetails && (
        <div style={{ borderTop: "1px solid var(--border)", marginTop: 8, paddingTop: 8 }}>
          {order.items.map((item, idx) => (
            <div key={idx} style={rows}>
              <span>{item.product_name} ({item.size}/{item.color}) × {item.quantity}</span>
              <b style={strong}>৳{item.subtotal}</b>
            </div>
          ))}
          <div style={{ ...rows, marginTop: 6 }}><span>Subtotal</span><b style={strong}>৳{order.subtotal}</b></div>
          <div style={rows}><span>Delivery</span><b style={strong}>৳{order.delivery_charge}</b></div>
          {order.customer_name && <div style={{ color: "var(--text-2)", marginTop: 6 }}>Name: <b style={strong}>{order.customer_name}</b></div>}
          {order.customer_phone && <div style={{ color: "var(--text-2)" }}>Phone: <b style={strong}>{order.customer_phone}</b></div>}
          {order.customer_address && <div style={{ color: "var(--text-2)" }}>Address: <b style={strong}>{order.customer_address}</b></div>}
        </div>
      )}

      <div style={{ color: "var(--text-2)", marginTop: showDetails ? 6 : 0 }}>Total: <b style={strong}>৳{order.total?.toLocaleString?.() ?? order.total}</b></div>
    </div>
  );
}

function CartMiniSummary({ data }) {
  if (!data.items.length) return null;
  return (
    <div style={{ background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 10, padding: 12, fontSize: 12, minWidth: 240 }}>
      {data.items.map((item) => (
        <div key={item.variant_id} style={{ display: "flex", justifyContent: "space-between", padding: "2px 0" }}>
          <span>{item.product_name} ({item.size}/{item.color}) × {item.quantity}</span>
          <span>৳{item.subtotal}</span>
        </div>
      ))}
      <div style={{ borderTop: "1px solid var(--border)", marginTop: 6, paddingTop: 6, display: "flex", justifyContent: "space-between", fontWeight: 700 }}>
        <span>Total</span>
        <span>৳{data.total}</span>
      </div>
    </div>
  );
}
