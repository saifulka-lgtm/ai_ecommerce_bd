import React, { useEffect, useState, useCallback } from "react";
import { api } from "../services/api";
import ProductCard from "./ProductCard";

export default function ProductGrid({ onAddToCart }) {
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState("");
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");

  useEffect(() => {
    api.listCategories().then(setCategories).catch(() => {});
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    api
      .searchProducts({ category: activeCategory || undefined, q: q || undefined, limit: 40 })
      .then(setProducts)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [activeCategory, q]);

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [load]);

  return (
    <section id="products" style={{ padding: "10px 28px 48px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12, marginBottom: 20 }}>
        <h2 style={{ fontSize: 22, fontWeight: 800, margin: 0 }}>Shop the collection</h2>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search products…"
          style={{
            background: "var(--bg-2)",
            border: "1px solid var(--border)",
            color: "var(--text-0)",
            borderRadius: 999,
            padding: "9px 16px",
            fontSize: 13,
            minWidth: 220,
          }}
        />
      </div>

      <div style={{ display: "flex", gap: 8, overflowX: "auto", paddingBottom: 14, marginBottom: 12 }}>
        <CategoryPill label="All" active={!activeCategory} onClick={() => setActiveCategory("")} />
        {categories.map((c) => (
          <CategoryPill key={c.id} label={c.name} active={activeCategory === c.name} onClick={() => setActiveCategory(c.name)} />
        ))}
      </div>

      {loading ? (
        <div style={{ color: "var(--text-2)", padding: "40px 0", textAlign: "center" }}>Loading products…</div>
      ) : products.length === 0 ? (
        <div style={{ color: "var(--text-2)", padding: "40px 0", textAlign: "center" }}>No products found.</div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
            gap: 18,
          }}
        >
          {products.map((p) => (
            <ProductCard key={p.id} product={p} onAddToCart={onAddToCart} />
          ))}
        </div>
      )}
    </section>
  );
}

function CategoryPill({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        whiteSpace: "nowrap",
        padding: "8px 16px",
        borderRadius: 999,
        fontSize: 13,
        fontWeight: 600,
        border: active ? "1px solid var(--bd-green-light)" : "1px solid var(--border)",
        background: active ? "rgba(0,145,95,0.15)" : "transparent",
        color: active ? "var(--bd-green-light)" : "var(--text-1)",
      }}
    >
      {label}
    </button>
  );
}
