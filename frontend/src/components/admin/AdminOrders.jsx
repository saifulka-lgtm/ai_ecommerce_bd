import React, { useEffect, useState } from "react";
import { api } from "../../services/api";
import AdminOrderAssistant from "./AdminOrderAssistant";

const STATUSES = ["PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"];

export default function AdminOrders({ token }) {
  const [orders, setOrders] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [expanded, setExpanded] = useState(null);
  const [loading, setLoading] = useState(true);

  const [events, setEvents] = useState([]);

  const load = (silent = false) => {
    if (silent !== true) setLoading(true);
    api.adminListOrders(token, statusFilter || undefined).then(setOrders).finally(() => setLoading(false));
    api.adminFulfillmentEvents(token, 15).then(setEvents).catch(() => {});
  };

  // The AI fulfillment agent changes statuses in the background, so refresh quietly.
  useEffect(() => {
    load();
    const timer = setInterval(() => load(true), 8000);
    return () => clearInterval(timer);
  }, [token, statusFilter]);

  const updateStatus = async (order, status) => {
    await api.adminUpdateOrderStatus(token, order.id, { order_status: status });
    load();
  };

  return (
    <div>
      <div style={{ background: "rgba(46,204,113,0.10)", border: "1px solid var(--border)", borderRadius: 10, padding: "10px 14px", marginBottom: 14, fontSize: 12, color: "var(--text-1)" }}>
        AI Fulfillment Agent চালু আছে — নতুন অর্ডার নিজে থেকেই PENDING → CONFIRMED → SHIPPED → DELIVERED হবে। অ্যাডমিনকে কিছু করতে হবে না।
      </div>
      <AdminOrderAssistant token={token} onChanged={load} />
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ margin: 0 }}>Orders ({orders.length})</h3>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{ background: "var(--bg-3)", border: "1px solid var(--border)", color: "var(--text-0)", borderRadius: 8, padding: "6px 10px", fontSize: 12 }}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {loading ? (
        <div style={{ color: "var(--text-2)" }}>Loading orders…</div>
      ) : orders.length === 0 ? (
        <div style={{ color: "var(--text-2)" }}>No orders yet.</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {orders.map((o) => (
            <div key={o.id} style={{ background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 10, padding: 14 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }} onClick={() => setExpanded(expanded === o.id ? null : o.id)}>
                <div>
                  <div style={{ fontWeight: 800, fontSize: 13 }}>{o.order_number} — {o.customer_name}</div>
                  <div style={{ fontSize: 11, color: "var(--text-2)" }}>{o.customer_phone} · {new Date(o.created_at).toLocaleString()}</div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontWeight: 700 }}>৳{o.total.toLocaleString()}</span>
                  <select
                    value={o.order_status}
                    onClick={(e) => e.stopPropagation()}
                    onChange={(e) => updateStatus(o, e.target.value)}
                    style={{ background: "var(--bg-3)", border: "1px solid var(--border)", color: "var(--text-0)", borderRadius: 6, padding: "4px 8px", fontSize: 11 }}
                  >
                    {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>

              {expanded === o.id && (
                <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid var(--border)", fontSize: 12 }}>
                  <div style={{ color: "var(--text-2)", marginBottom: 6 }}>Delivery address: {o.customer_address}</div>
                  <div style={{ color: "var(--text-2)", marginBottom: 6 }}>
                    Payment: {o.payment_method} — <b>{o.payment_status}</b>
                  </div>
                  {o.items.map((item, i) => (
                    <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0" }}>
                      <span>{item.product_name} ({item.size}/{item.color}) × {item.quantity}</span>
                      <span>৳{item.subtotal}</span>
                    </div>
                  ))}
                  <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 700, marginTop: 6, paddingTop: 6, borderTop: "1px solid var(--border)" }}>
                    <span>Total</span>
                    <span>৳{o.total}</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {events.length > 0 && (
        <div style={{ marginTop: 22 }}>
          <h4 style={{ margin: "0 0 8px" }}>AI Fulfillment Activity</h4>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {events.map((ev) => (
              <div key={ev.id} style={{ background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 12px", fontSize: 12, display: "flex", justifyContent: "space-between" }}>
                <span><b>{ev.order_number}</b>: {ev.from_status} → <b style={{ color: "var(--bd-green-light)" }}>{ev.to_status}</b></span>
                <span style={{ color: "var(--text-2)" }}>{ev.actor} · {new Date(ev.created_at + "Z").toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
