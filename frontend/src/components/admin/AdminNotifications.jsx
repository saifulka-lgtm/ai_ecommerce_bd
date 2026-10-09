import React from "react";

const TYPE_STYLE = {
  OUT_OF_STOCK: { color: "#e74c3c", label: "Out of stock" },
  LOW_STOCK: { color: "#f1c40f", label: "Low stock" },
};

export default function AdminNotifications({ items, unread, onMarkRead }) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>AI Notifications {unread > 0 && <span style={{ color: "var(--text-2)", fontSize: 13 }}>({unread} নতুন)</span>}</h3>
        <button
          onClick={onMarkRead}
          disabled={unread === 0}
          style={{ background: "var(--bg-3)", border: "1px solid var(--border)", color: "var(--text-1)", borderRadius: 8, padding: "6px 12px", fontSize: 12, cursor: unread ? "pointer" : "default", opacity: unread ? 1 : 0.5 }}
        >
          সব পড়া হয়েছে
        </button>
      </div>
      <p style={{ color: "var(--text-2)", fontSize: 12, marginTop: -4 }}>
        AI নিজে থেকেই স্টক কমে গেলে বা শেষ হয়ে গেলে এখানে জানিয়ে দেয়।
      </p>

      {items.length === 0 ? (
        <div style={{ color: "var(--text-2)" }}>কোনো নোটিফিকেশন নেই।</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {items.map((n) => {
            const st = TYPE_STYLE[n.type] || { color: "var(--text-2)", label: n.type };
            return (
              <div key={n.id} style={{ background: "var(--bg-2)", border: "1px solid var(--border)", borderLeft: `4px solid ${st.color}`, borderRadius: 10, padding: 12, fontSize: 12, opacity: n.is_read ? 0.65 : 1 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <b style={{ color: st.color }}>{n.title}{!n.is_read && " •"}</b>
                  <span style={{ color: "var(--text-2)" }}>{new Date(n.created_at + "Z").toLocaleString()}</span>
                </div>
                <div>{n.message}</div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
