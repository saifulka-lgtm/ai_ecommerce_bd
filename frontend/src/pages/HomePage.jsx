import React, { useState } from "react";
import Header from "../components/Header";
import Hero from "../components/Hero";
import ProductGrid from "../components/ProductGrid";
import ChatPanel from "../components/ChatPanel";
import CartDrawer from "../components/CartDrawer";
import { useSession } from "../hooks/useSession";
import { useCart } from "../hooks/useCart";
import { api } from "../services/api";

export default function HomePage() {
  const sessionId = useSession();
  const { cart, refreshCart } = useCart(sessionId);
  const [cartOpen, setCartOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = (text) => {
    setToast(text);
    setTimeout(() => setToast(null), 2500);
  };

  const handleAddToCart = async (product, size, color) => {
    try {
      const full = await api.getProduct(product.id);
      const variant = full.variants.find((v) => v.size === size && v.color === color) || full.variants[0];
      if (!variant) throw new Error("No variant available");
      if (variant.stock <= 0) throw new Error("That size/color is out of stock");
      await api.addToCart(sessionId, variant.id, 1);
      await refreshCart();
      showToast(`Added ${product.name} (${variant.size}/${variant.color}) to cart`);
    } catch (e) {
      showToast(e.message);
    }
  };

  return (
    <div>
      <Header cartCount={cart.item_count} onCartClick={() => setCartOpen(true)} onChatClick={() => setChatOpen(true)} />
      <Hero onAskAI={() => setChatOpen(true)} />
      <ProductGrid onAddToCart={handleAddToCart} />
      <ChatPanel
        sessionId={sessionId}
        onAddToCart={handleAddToCart}
        onOpenCart={() => refreshCart()}
        open={chatOpen}
        onOpen={() => setChatOpen(true)}
        onClose={() => setChatOpen(false)}
      />

      <CartDrawer open={cartOpen} onClose={() => setCartOpen(false)} sessionId={sessionId} cart={cart} refreshCart={refreshCart} />

      {toast && (
        <div
          style={{
            position: "fixed",
            bottom: 24,
            left: "50%",
            transform: "translateX(-50%)",
            background: "var(--bg-3)",
            border: "1px solid var(--border)",
            color: "var(--text-0)",
            padding: "12px 20px",
            borderRadius: 999,
            fontSize: 13,
            boxShadow: "var(--shadow)",
            zIndex: 100,
          }}
        >
          {toast}
        </div>
      )}

      <footer style={{ textAlign: "center", padding: "24px", color: "var(--text-2)", fontSize: 12, borderTop: "1px solid var(--border)" }}>
        Fashion BD — a testing/demo project. No real payments are processed.
      </footer>
    </div>
  );
}
