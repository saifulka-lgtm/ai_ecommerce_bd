import React, { useState } from "react";
import { api } from "../services/api";
import CheckoutForm from "./CheckoutForm";

export default function CartDrawer({ open, onClose, sessionId, cart, refreshCart }) {
  const [mode, setMode] = useState("cart"); // cart | checkout | confirmed
  const [lastOrder, setLastOrder] = useState(null);
  const [busyVariant, setBusyVariant] = useState(null);

  if (!open) return null;

  const changeQty = async (variantId, qty) => {
    setBusyVariant(variantId);
    try {
      if (qty <= 0) {
        await api.removeCartItem(sessionId, variantId);
      } else {
        await api.updateCartItem(sessionId, variantId, qty);
      }
      await refreshCart();
    } catch (e) {
      alert(e.message);
    } finally {
      setBusyVariant(null);
    }
  };

  const handleOrderCreated = async (order) => {
    setLastOrder(order);
    setMode("confirmed");
    await refreshCart();
  };

  const closeAndReset = () => {
    setMode("cart");
    setLastOrder(null);
    onClose();
  };

  return (
    <>
      <div
        onClick={closeAndReset}
        style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", zIndex: 60 }}
      />
      <aside
        className="fade-in-up"
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          bottom: 0,
          width: "min(420px, 100vw)",
          background: "var(--bg-1)",
          borderLeft: "1px solid var(--border)",
          zIndex: 61,
          display: "flex",
          flexDirection: "column",
          animation: "slideInRight 0.25s ease",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "18px 20px", borderBottom: "1px solid var(--border)" }}>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 800 }}>
            {mode === "cart" ? "Your Cart" : mode === "checkout" ? "Checkout" : "Order Confirmed"}
          </h3>
          <button onClick={closeAndReset} style={{ background: "none", border: "none", color: "var(--text-1)", fontSize: 20 }}>×</button>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: 20 }}>
          {mode === "cart" && (
            cart.items.length === 0 ? (
              <div style={{ color: "var(--text-2)", textAlign: "center", marginTop: 40 }}>Your cart is empty.</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {cart.items.map((item) => (
                  <div key={item.variant_id} style={{ display: "flex", gap: 12, borderBottom: "1px solid var(--border)", paddingBottom: 14 }}>
                    <img src={item.image} alt={item.product_name} style={{ width: 60, height: 74, objectFit: "cover", borderRadius: 8 }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 700, fontSize: 13 }}>{item.product_name}</div>
                      <div style={{ fontSize: 12, color: "var(--text-2)" }}>{item.size} / {item.color}</div>
                      <div style={{ fontSize: 13, fontWeight: 700, marginTop: 4 }}>৳{item.unit_price.toLocaleString()}</div>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 6 }}>
                        <QtyButton disabled={busyVariant === item.variant_id} onClick={() => changeQty(item.variant_id, item.quantity - 1)}>−</QtyButton>
                        <span style={{ fontSize: 13, minWidth: 16, textAlign: "center" }}>{item.quantity}</span>
                        <QtyButton disabled={busyVariant === item.variant_id} onClick={() => changeQty(item.variant_id, item.quantity + 1)}>+</QtyButton>
                        <button
                          onClick={() => changeQty(item.variant_id, 0)}
                          style={{ marginLeft: "auto", background: "none", border: "none", color: "var(--bd-red-light)", fontSize: 12 }}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )
          )}

          {mode === "checkout" && (
            <CheckoutForm sessionId={sessionId} onOrderCreated={handleOrderCreated} onCancel={() => setMode("cart")} />
          )}

          {mode === "confirmed" && lastOrder && (
            <div style={{ textAlign: "center", padding: "20px 0" }}>
              <div style={{ fontSize: 40 }}>✅</div>
              <h4 style={{ margin: "10px 0 4px" }}>Order placed!</h4>
              <p style={{ color: "var(--text-1)", fontSize: 13 }}>Your demo order has been created.</p>
              <div style={{ background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 10, padding: 16, marginTop: 16, textAlign: "left", fontSize: 13, display: "flex", flexDirection: "column", gap: 6 }}>
                <Row label="Order ID" value={lastOrder.order_number} strong />
                <Row label="Total" value={`৳${lastOrder.total.toLocaleString()}`} />
                <Row label="Payment" value={lastOrder.payment_status} />
                <Row label="Status" value={lastOrder.order_status} />
              </div>
              <button className="btn-primary" onClick={closeAndReset} style={{ marginTop: 18, borderRadius: 8, padding: "10px 24px", fontSize: 13, fontWeight: 700 }}>
                Continue Shopping
              </button>
            </div>
          )}
        </div>

        {mode === "cart" && cart.items.length > 0 && (
          <div style={{ padding: 20, borderTop: "1px solid var(--border)" }}>
            <Row label="Subtotal" value={`৳${cart.subtotal.toLocaleString()}`} />
            <Row label="Delivery" value={cart.delivery_charge ? `৳${cart.delivery_charge.toLocaleString()}` : "Free"} />
            <div style={{ borderTop: "1px solid var(--border)", margin: "8px 0" }} />
            <Row label="Total" value={`৳${cart.total.toLocaleString()}`} strong />
            <button
              className="btn-primary"
              onClick={() => setMode("checkout")}
              style={{ width: "100%", marginTop: 14, borderRadius: 8, padding: "12px 0", fontSize: 14, fontWeight: 700 }}
            >
              Proceed to Checkout
            </button>
          </div>
        )}
      </aside>
    </>
  );
}

function QtyButton({ children, ...props }) {
  return (
    <button
      {...props}
      style={{
        width: 26,
        height: 26,
        borderRadius: 6,
        border: "1px solid var(--border)",
        background: "var(--bg-3)",
        color: "var(--text-0)",
        fontSize: 14,
        lineHeight: 1,
      }}
    >
      {children}
    </button>
  );
}

function Row({ label, value, strong }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: strong ? 15 : 13, fontWeight: strong ? 800 : 400, color: strong ? "var(--text-0)" : "var(--text-1)", padding: "3px 0" }}>
      <span>{label}</span>
      <span>{value}</span>
    </div>
  );
}
