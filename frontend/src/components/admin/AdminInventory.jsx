import React, { useEffect, useState } from "react";
import { api } from "../../services/api";

const STATUS_STYLE = {
  OK: { label: "In stock", color: "#2ecc71" },
  LOW: { label: "Low stock", color: "#f1c40f" },
  OUT_OF_STOCK: { label: "Out of stock", color: "#e74c3c" },
};

function Badge({ status }) {
  const st = STATUS_STYLE[status] || STATUS_STYLE.OK;
  return (
    <span style={{ padding: "3px 10px", borderRadius: 999, fontSize: 11, fontWeight: 700, background: "var(--bg-3)", border: `1px solid ${st.color}`, color: st.color, whiteSpace: "nowrap" }}>
      {st.label}
    </span>
  );
}

export default function AdminInventory({ token }) {
  const [data, setData] = useState(null);
  const [movements, setMovements] = useState([]);
  const [filter, setFilter] = useState("ALL");
  const [expanded, setExpanded] = useState(null);

  const load = () => {
    api.adminInventory(token).then(setData).catch(() => {});
    api.adminStockMovements(token, 20).then(setMovements).catch(() => {});
  };

  // Stock changes whenever a customer orders, so refresh quietly.
  useEffect(() => {
    load();
    const timer = setInterval(load, 8000);
    return () => clearInterval(timer);
  }, [token]);

  if (!data) return <div style={{ color: "var(--text-2)" }}>Loading inventory…</div>;

  const { summary, products } = data;
  const shown = products.filter((p) => filter === "ALL" || p.status === filter);

  const cards = [
    { label: "Products", value: summary.total_products },
    { label: "Total units in stock", value: summary.total_units.toLocaleString() },
    { label: `Low stock variants (≤ ${summary.low_stock_threshold})`, value: summary.low_stock_variants },
    { label: "Out-of-stock variants", value: summary.out_of_stock_variants },
  ];

  return (
    <div>
      <div style={{ background: "rgba(46,204,113,0.10)", border: "1px solid var(--border)", borderRadius: 10, padding: "10px 14px", marginBottom: 14, fontSize: 12, color: "var(--text-1)" }}>
        স্টক নিজে থেকেই কমে/বাড়ে — কাস্টমার অর্ডার করলে কমে, অর্ডার বাতিল হলে ফিরে আসে। এখানে আপনি শুধু ট্র্যাক করতে পারবেন।
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: 18 }}>
        {cards.map((c) => (
          <div key={c.label} style={{ background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 12, padding: 16 }}>
            <div style={{ fontSize: 24, fontWeight: 800 }}>{c.value}</div>
            <div style={{ fontSize: 11, color: "var(--text-2)", marginTop: 4 }}>{c.label}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>Stock by product ({shown.length})</h3>
        <select value={filter} onChange={(e) => setFilter(e.target.value)} style={{ background: "var(--bg-3)", border: "1px solid var(--border)", color: "var(--text-0)", borderRadius: 8, padding: "6px 10px", fontSize: 12 }}>
          <option value="ALL">All</option>
          <option value="OK">In stock</option>
          <option value="LOW">Low stock</option>
          <option value="OUT_OF_STOCK">Out of stock</option>
        </select>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {shown.map((p) => (
          <div key={p.product_id} style={{ background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 10, padding: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }} onClick={() => setExpanded(expanded === p.product_id ? null : p.product_id)}>
              <div>
                <div style={{ fontWeight: 800, fontSize: 13 }}>{p.name}</div>
                <div style={{ fontSize: 11, color: "var(--text-2)" }}>{p.category} · {p.sku}{p.active ? "" : " · inactive"}</div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <b>{p.total_stock} pcs</b>
                <Badge status={p.status} />
              </div>
            </div>

            {expanded === p.product_id && (
              <div style={{ marginTop: 10, paddingTop: 10, borderTop: "1px solid var(--border)", display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: 8 }}>
                {p.variants.map((v, i) => (
                  <div key={i} style={{ background: "var(--bg-3)", borderRadius: 8, padding: "8px 10px", fontSize: 12 }}>
                    <div>{v.size} / {v.color}</div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 4 }}>
                      <b>{v.stock}</b>
                      <Badge status={v.status} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {movements.length > 0 && (
        <div style={{ marginTop: 22 }}>
          <h4 style={{ margin: "0 0 8px" }}>Recent stock movements</h4>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {movements.map((m) => (
              <div key={m.id} style={{ background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 12px", fontSize: 12, display: "flex", justifyContent: "space-between", gap: 12 }}>
                <span>
                  <b style={{ color: m.change < 0 ? "#e74c3c" : "#2ecc71" }}>{m.change > 0 ? `+${m.change}` : m.change}</b>{" "}
                  {m.product_name} ({m.size}/{m.color}) → <b>{m.stock_after}</b> left · {m.reason}
                </span>
                <span style={{ color: "var(--text-2)", whiteSpace: "nowrap" }}>{new Date(m.created_at + "Z").toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
