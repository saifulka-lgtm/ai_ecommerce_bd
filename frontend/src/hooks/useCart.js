import { useCallback, useEffect, useState } from "react";
import { api } from "../services/api";

export function useCart(sessionId) {
  const [cart, setCart] = useState({ items: [], subtotal: 0, delivery_charge: 0, total: 0, item_count: 0 });
  const [loading, setLoading] = useState(false);

  const refreshCart = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const data = await api.getCart(sessionId);
      setCart(data);
    } catch (e) {
      console.error("Failed to load cart", e);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    refreshCart();
  }, [refreshCart]);

  return { cart, refreshCart, loading };
}
