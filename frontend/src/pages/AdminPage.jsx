import React, { useState } from "react";
import { Link } from "react-router-dom";
import AdminLogin from "../components/admin/AdminLogin";
import AdminDashboard from "../components/admin/AdminDashboard";
import AdminProducts from "../components/admin/AdminProducts";
import AdminOrders from "../components/admin/AdminOrders";
import AdminInventory from "../components/admin/AdminInventory";
import AdminAILogs from "../components/admin/AdminAILogs";

const TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "products", label: "Products" },
  { id: "orders", label: "Orders" },
  { id: "inventory", label: "Inventory" },
  { id: "ai-logs", label: "AI Activity" },
];

export default function AdminPage() {
  const [token, setToken] = useState(() => localStorage.getItem("admin_token") || "");
  const [tab, setTab] = useState("dashboard");

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
            </button>
          ))}
        </nav>
        <button onClick={logout} style={{ marginTop: "auto", background: "none", border: "1px solid var(--border)", color: "var(--text-2)", borderRadius: 8, padding: "8px 0", fontSize: 12 }}>
          Log out
        </button>
      </aside>

      <main style={{ flex: 1, padding: 32, overflowY: "auto" }}>
        {tab === "dashboard" && <AdminDashboard token={token} />}
        {tab === "products" && <AdminProducts token={token} />}
        {tab === "orders" && <AdminOrders token={token} />}
        {tab === "inventory" && <AdminInventory token={token} />}
        {tab === "ai-logs" && <AdminAILogs token={token} />}
      </main>
    </div>
  );
}
