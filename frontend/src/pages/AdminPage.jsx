import React, { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import AdminLogin from "../components/admin/AdminLogin";
import AdminDashboard from "../components/admin/AdminDashboard";
import AdminProducts from "../components/admin/AdminProducts";
import AdminOrders from "../components/admin/AdminOrders";
import AdminInventory from "../components/admin/AdminInventory";
import AdminNotifications from "../components/admin/AdminNotifications";
import { api } from "../services/api";
import AdminAILogs from "../components/admin/AdminAILogs";

const TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "products", label: "Products" },
  { id: "orders", label: "Orders" },
  { id: "inventory", label: "Inventory" },
  { id: "notifications", label: "Notifications" },
  { id: "ai-logs", label: "AI Activity" },
];

export default function AdminPage() {
  const [token, setToken] = useState(() => localStorage.getItem("admin_token") || "");
  const [tab, setTab] = useState("dashboard");
  const [notif, setNotif] = useState({ unread_count: 0, items: [] });
  const [toast, setToast] = useState(null);
  const lastUnread = useRef(0);

  // The AI raises alerts on its own (low / out of stock), so poll quietly.
  useEffect(() => {
    if (!token) return undefined;
    const poll = () =>
      api.adminNotifications(token).then((data) => {
        if (data.unread_count > lastUnread.current && data.items[0]) {
          setToast(data.items.find((n) => !n.is_read) || data.items[0]);
          setTimeout(() => setToast(null), 7000);
        }
        lastUnread.current = data.unread_count;
        setNotif(data);
      }).catch(() => {});
    poll();
    const timer = setInterval(poll, 8000);
    return () => clearInterval(timer);
  }, [token]);

  const markRead = () => {
    api.adminMarkNotificationsRead(token).then(() => {
      lastUnread.current = 0;
      setNotif((n) => ({ unread_count: 0, items: n.items.map((i) => ({ ...i, is_read: true })) }));
    });
  };

  const handleLogin = (t) => {
    localStorage.setItem("admin_token", t);
    setToken(t);
  };

  const logout = () => {
    localStorage.removeItem("admin_token");
    setToken("");
  };

  if (!token) return <AdminLogin onLoggedIn={handleLogin} />;

  return (
    <div style={{ minHeight: "100vh", display: "flex" }}>
      <aside style={{ width: 220, borderRight: "1px solid var(--border)", padding: 20, display: "flex", flexDirection: "column" }}>
        <Link to="/" style={{ fontWeight: 800, fontSize: 16, marginBottom: 30, display: "block" }}>
          ← Fashion BD
        </Link>
        <nav style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                textAlign: "left",
                padding: "10px 14px",
                borderRadius: 8,
                border: "none",
                background: tab === t.id ? "var(--bg-2)" : "transparent",
                color: tab === t.id ? "var(--bd-green-light)" : "var(--text-1)",
                fontWeight: tab === t.id ? 700 : 500,
                fontSize: 13,
              }}
            >
              {t.label}
              {t.id === "notifications" && notif.unread_count > 0 && (
                <span style={{ marginLeft: 8, background: "#e74c3c", color: "#fff", borderRadius: 999, padding: "1px 7px", fontSize: 10, fontWeight: 800 }}>
                  {notif.unread_count}
                </span>
              )}
            </button>
          ))}
        </nav>
        <button onClick={logout} style={{ marginTop: "auto", background: "none", border: "1px solid var(--border)", color: "var(--text-2)", borderRadius: 8, padding: "8px 0", fontSize: 12 }}>
          Log out
        </button>
      </aside>

      {toast && (
        <div
          onClick={() => { setToast(null); setTab("notifications"); }}
          style={{ position: "fixed", top: 20, right: 20, zIndex: 200, maxWidth: 340, background: "var(--bg-2)", border: "1px solid var(--border)", borderLeft: `4px solid ${toast.type === "OUT_OF_STOCK" ? "#e74c3c" : "#f1c40f"}`, borderRadius: 10, padding: "12px 14px", fontSize: 12, cursor: "pointer", boxShadow: "0 8px 24px rgba(0,0,0,0.4)" }}
        >
          <b>{toast.title}</b>
          <div style={{ marginTop: 4, color: "var(--text-1)" }}>{toast.message}</div>
        </div>
      )}

      <main style={{ flex: 1, padding: 32, overflowY: "auto" }}>
        {tab === "dashboard" && <AdminDashboard token={token} />}
        {tab === "products" && <AdminProducts token={token} />}
        {tab === "orders" && <AdminOrders token={token} />}
        {tab === "inventory" && <AdminInventory token={token} />}
        {tab === "notifications" && <AdminNotifications items={notif.items} unread={notif.unread_count} onMarkRead={markRead} />}
        {tab === "ai-logs" && <AdminAILogs token={token} />}
      </main>
    </div>
  );
}
