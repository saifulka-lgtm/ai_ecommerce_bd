import React, { useEffect, useState } from "react";
import { api } from "../../services/api";

export default function AdminDashboard({ token }) {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.adminDashboard(token).then(setStats).catch(() => {});
  }, [token]);

  if (!stats) return <div style={{ color: "var(--text-2)" }}>Loading dashboard…</div>;

  const cards = [
    { label: "Total Products", value: stats.total_products, icon: "👕" },
    { label: "Total Orders", value: stats.total_orders, icon: "📦" },
    { label: "Pending Orders", value: stats.pending_orders, icon: "⏳" },
    { label: "Completed Orders", value: stats.completed_orders, icon: "✅" },
    { label: "Demo Sales", value: `৳${stats.demo_sales_amount.toLocaleString()}`, icon: "💰" },
    { label: "Low Stock Products", value: stats.low_stock_products, icon: "⚠️" },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
      {cards.map((c) => (
        <div key={c.label} style={{ background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 22 }}>{c.icon}</div>
          <div style={{ fontSize: 26, fontWeight: 800, margin: "10px 0 4px" }}>{c.value}</div>
          <div style={{ fontSize: 12, color: "var(--text-2)" }}>{c.label}</div>
        </div>
      ))}
    </div>
  );
}
