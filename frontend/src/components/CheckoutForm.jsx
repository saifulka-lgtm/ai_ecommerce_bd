import React, { useState } from "react";
import { api } from "../services/api";

const PAYMENT_OPTIONS = [
  { value: "demo_cod", label: "Cash on Delivery" },
  { value: "demo_card", label: "Card" },
  { value: "demo_mobile", label: "Mobile (bKash/Nagad)" },
];

export default function CheckoutForm({ sessionId, onOrderCreated, onCancel }) {
  const [form, setForm] = useState({ customer_name: "", customer_phone: "", customer_address: "", payment_method: "demo_cod" });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const order = await api.createOrder({ session_id: sessionId, ...form });
      onOrderCreated(order);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const inputStyle = {
    width: "100%",
    background: "var(--bg-3)",
    border: "1px solid var(--border)",
    color: "var(--text-0)",
    borderRadius: 8,
    padding: "10px 12px",
    fontSize: 13,
  };

  return (
    <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div
        style={{
          background: "rgba(244,42,65,0.1)",
          border: "1px solid var(--bd-red)",
          borderRadius: 8,
          padding: "8px 12px",
          fontSize: 11,
          fontWeight: 700,
          color: "var(--bd-red-light)",
          textAlign: "center",
        }}
      >
        DEMO PAYMENT — NO REAL MONEY IS CHARGED
      </div>

      <label style={{ fontSize: 12, color: "var(--text-1)" }}>
        Full name
        <input required style={{ ...inputStyle, marginTop: 4 }} value={form.customer_name} onChange={update("customer_name")} placeholder="e.g. Rahim Uddin" />
      </label>
      <label style={{ fontSize: 12, color: "var(--text-1)" }}>
        Phone number
        <input required style={{ ...inputStyle, marginTop: 4 }} value={form.customer_phone} onChange={update("customer_phone")} placeholder="e.g. 01711223344" />
      </label>
      <label style={{ fontSize: 12, color: "var(--text-1)" }}>
        Delivery address
        <textarea required rows={2} style={{ ...inputStyle, marginTop: 4, resize: "vertical" }} value={form.customer_address} onChange={update("customer_address")} placeholder="House, Road, Area, City" />
      </label>
      <label style={{ fontSize: 12, color: "var(--text-1)" }}>
        Payment method
        <select style={{ ...inputStyle, marginTop: 4 }} value={form.payment_method} onChange={update("payment_method")}>
          {PAYMENT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </label>

      {error && <div style={{ color: "var(--bd-red-light)", fontSize: 12 }}>{error}</div>}

      <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
        <button type="button" onClick={onCancel} style={{ flex: 1, background: "transparent", border: "1px solid var(--border)", color: "var(--text-1)", borderRadius: 8, padding: "10px 0", fontSize: 13 }}>
          Back
        </button>
        <button type="submit" disabled={submitting} className="btn-primary" style={{ flex: 2, borderRadius: 8, padding: "10px 0", fontSize: 13, fontWeight: 700 }}>
          {submitting ? "Placing order…" : "Confirm & Place Order"}
        </button>
      </div>
    </form>
  );
}
