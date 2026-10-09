import React, { useState } from "react";

export default function ProductCard({ product, onAddToCart, onView, compact = false }) {
  const [expanded, setExpanded] = useState(false);
  const [size, setSize] = useState(product.sizes?.[0] || "");
  const [color, setColor] = useState(product.colors?.[0] || "");
  const [adding, setAdding] = useState(false);

  const hasDiscount = product.sale_price && product.sale_price < product.price;
  const price = product.effective_price ?? product.sale_price ?? product.price;

  const handleAddClick = async () => {
    if (!expanded) {
      setExpanded(true);
      return;
    }
    setAdding(true);
    try {
      await onAddToCart(product, size, color);
      setExpanded(false);
    } finally {
      setAdding(false);
    }
  };

  return (
    <div
      className="card-hover fade-in-up"
      style={{
        background: "var(--bg-2)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius)",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        width: compact ? 180 : "100%",
        flexShrink: 0,
      }}
    >
      <div style={{ position: "relative", aspectRatio: "4/5", background: "var(--bg-3)" }}>
        <img
          src={product.image}
          alt={product.name}
          loading="lazy"
          style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
        />
        {hasDiscount && (
          <span
            style={{
              position: "absolute",
              top: 10,
              left: 10,
              background: "var(--bd-red)",
              color: "white",
              fontSize: 11,
              fontWeight: 700,
              padding: "3px 8px",
              borderRadius: 6,
            }}
          >
            SALE
          </span>
        )}
        {!product.in_stock && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              background: "rgba(10,15,13,0.65)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 13,
              fontWeight: 700,
              color: "var(--text-1)",
              letterSpacing: 1,
            }}
          >
            OUT OF STOCK
          </div>
        )}
      </div>

      <div style={{ padding: compact ? "10px 12px" : "14px 16px", display: "flex", flexDirection: "column", gap: 6, flex: 1 }}>
        <div style={{ fontSize: 11, color: "var(--bd-green-light)", fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>
          {product.category}
        </div>
        <div style={{ fontWeight: 700, fontSize: compact ? 13 : 15, lineHeight: 1.3 }}>{product.name}</div>

        <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
          <span style={{ fontWeight: 800, fontSize: compact ? 14 : 17 }}>৳{price.toLocaleString()}</span>
          {hasDiscount && (
            <span style={{ fontSize: 12, color: "var(--text-2)", textDecoration: "line-through" }}>
              ৳{product.price.toLocaleString()}
            </span>
          )}
        </div>

        {!compact && (
          <div style={{ fontSize: 12, color: "var(--text-2)" }}>
            Sizes: {product.sizes?.join(", ") || "-"} · Colors: {product.colors?.join(", ") || "-"}
          </div>
        )}

        {expanded && (
          <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
            <select
              value={size}
              onChange={(e) => setSize(e.target.value)}
              style={{ flex: 1, background: "var(--bg-3)", color: "var(--text-0)", border: "1px solid var(--border)", borderRadius: 8, padding: "6px 8px", fontSize: 12 }}
            >
              {product.sizes?.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <select
              value={color}
              onChange={(e) => setColor(e.target.value)}
              style={{ flex: 1, background: "var(--bg-3)", color: "var(--text-0)", border: "1px solid var(--border)", borderRadius: 8, padding: "6px 8px", fontSize: 12 }}
            >
              {product.colors?.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        )}

        <div style={{ display: "flex", gap: 8, marginTop: "auto", paddingTop: 8 }}>
          {onView && (
            <button
              onClick={() => onView(product)}
              style={{
                flex: 1,
                background: "transparent",
                border: "1px solid var(--border)",
                color: "var(--text-1)",
                borderRadius: 8,
                padding: "8px 0",
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              View
            </button>
          )}
          <button
            className="btn-primary"
            disabled={!product.in_stock || adding}
            onClick={handleAddClick}
            style={{ flex: 1.4, borderRadius: 8, padding: "8px 0", fontSize: 12, fontWeight: 700 }}
          >
            {adding ? "Adding…" : expanded ? "Confirm" : "Add to Cart"}
          </button>
        </div>
      </div>
    </div>
  );
}
