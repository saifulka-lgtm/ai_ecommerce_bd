import React, { useEffect, useState } from "react";
import { api } from "../../services/api";

const inputStyle = {
  background: "var(--bg-3)",
  border: "1px solid var(--border)",
  color: "var(--text-0)",
  borderRadius: 6,
  padding: "6px 8px",
  fontSize: 12,
};

export default function AdminProducts({ token }) {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([api.adminListProducts(token), api.listCategories()])
      .then(([p, c]) => {
        setProducts(p);
        setCategories(c);
      })
      .finally(() => setLoading(false));
  };

  useEffect(load, [token]);

  const toggleActive = async (product) => {
    await api.adminUpdateProduct(token, product.id, { active: !product.active });
    load();
  };

  const updateVariantStock = async (variantId, stock) => {
    await api.adminUpdateVariant(token, variantId, { stock: Number(stock) });
    load();
  };

  const deleteProduct = async (id) => {
    if (!confirm("Delete this product permanently?")) return;
    await api.adminDeleteProduct(token, id);
    load();
  };

  if (loading) return <div style={{ color: "var(--text-2)" }}>Loading products…</div>;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ margin: 0 }}>Products ({products.length})</h3>
        <button className="btn-primary" onClick={() => setShowAdd((s) => !s)} style={{ borderRadius: 8, padding: "8px 16px", fontSize: 13, fontWeight: 700 }}>
          {showAdd ? "Close" : "+ Add Product"}
        </button>
      </div>

      {showAdd && (
        <AddProductForm
          token={token}
          categories={categories}
          onCreated={() => {
            setShowAdd(false);
            load();
          }}
        />
      )}

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ textAlign: "left", color: "var(--text-2)", fontSize: 11, textTransform: "uppercase" }}>
              <th style={th}>Product</th>
              <th style={th}>Category</th>
              <th style={th}>Price</th>
              <th style={th}>Variants (size/color/stock)</th>
              <th style={th}>Active</th>
              <th style={th}></th>
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id} style={{ borderTop: "1px solid var(--border)" }}>
                <td style={td}>
                  <div style={{ fontWeight: 700 }}>{p.name}</div>
                  <div style={{ color: "var(--text-2)", fontSize: 11 }}>{p.sku}</div>
                </td>
                <td style={td}>{p.category?.name}</td>
                <td style={td}>
                  ৳{p.price}
                  {p.sale_price ? <div style={{ color: "var(--bd-red-light)" }}>sale ৳{p.sale_price}</div> : null}
                </td>
                <td style={td}>
                  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    {p.variants.map((v) => (
                      <div key={v.id} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <span style={{ color: "var(--text-2)", minWidth: 70 }}>{v.size}/{v.color}</span>
                        <input
                          type="number"
                          defaultValue={v.stock}
                          onBlur={(e) => e.target.value !== String(v.stock) && updateVariantStock(v.id, e.target.value)}
                          style={{ ...inputStyle, width: 60 }}
                        />
                      </div>
                    ))}
                  </div>
                </td>
                <td style={td}>
                  <button
                    onClick={() => toggleActive(p)}
                    style={{
                      fontSize: 11,
                      padding: "4px 10px",
                      borderRadius: 999,
                      border: "1px solid var(--border)",
                      background: p.active ? "rgba(46,204,113,0.15)" : "rgba(244,42,65,0.15)",
                      color: p.active ? "var(--success)" : "var(--bd-red-light)",
                    }}
                  >
                    {p.active ? "Active" : "Hidden"}
                  </button>
                </td>
                <td style={td}>
                  <button onClick={() => deleteProduct(p.id)} style={{ background: "none", border: "none", color: "var(--bd-red-light)", fontSize: 12 }}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const th = { padding: "8px 10px" };
const td = { padding: "10px 10px", verticalAlign: "top" };

function AddProductForm({ token, categories, onCreated }) {
  const [form, setForm] = useState({ name: "", category_id: categories[0]?.id || "", price: "", sale_price: "", sku: "", image: "", description: "" });
  const [variants, setVariants] = useState([{ size: "M", color: "Black", stock: 10 }]);
  const [error, setError] = useState("");

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  const updateVariant = (i, field, value) => setVariants((vs) => vs.map((v, idx) => (idx === i ? { ...v, [field]: value } : v)));
  const addVariantRow = () => setVariants((vs) => [...vs, { size: "M", color: "Black", stock: 0 }]);
  const removeVariantRow = (i) => setVariants((vs) => vs.filter((_, idx) => idx !== i));

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await api.adminCreateProduct(token, {
        ...form,
        price: Number(form.price),
        sale_price: form.sale_price ? Number(form.sale_price) : null,
        image: form.image || `https://picsum.photos/seed/${form.sku || Date.now()}/400/500`,
        variants: variants.map((v) => ({ ...v, stock: Number(v.stock) })),
      });
      onCreated();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <form onSubmit={submit} style={{ background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 12, padding: 18, marginBottom: 20, display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr", gap: 10 }}>
        <input required placeholder="Product name" value={form.name} onChange={update("name")} style={inputStyle} />
        <select value={form.category_id} onChange={update("category_id")} style={inputStyle}>
          {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <input required placeholder="SKU" value={form.sku} onChange={update("sku")} style={inputStyle} />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 2fr", gap: 10 }}>
        <input required type="number" placeholder="Price (৳)" value={form.price} onChange={update("price")} style={inputStyle} />
        <input type="number" placeholder="Sale price (optional)" value={form.sale_price} onChange={update("sale_price")} style={inputStyle} />
        <input placeholder="Image URL (optional)" value={form.image} onChange={update("image")} style={inputStyle} />
      </div>
      <textarea placeholder="Description" value={form.description} onChange={update("description")} rows={2} style={{ ...inputStyle, resize: "vertical" }} />

      <div>
        <div style={{ fontSize: 12, color: "var(--text-2)", marginBottom: 6 }}>Variants</div>
        {variants.map((v, i) => (
          <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6 }}>
            <input placeholder="Size" value={v.size} onChange={(e) => updateVariant(i, "size", e.target.value)} style={{ ...inputStyle, width: 70 }} />
            <input placeholder="Color" value={v.color} onChange={(e) => updateVariant(i, "color", e.target.value)} style={{ ...inputStyle, width: 100 }} />
            <input type="number" placeholder="Stock" value={v.stock} onChange={(e) => updateVariant(i, "stock", e.target.value)} style={{ ...inputStyle, width: 80 }} />
            {variants.length > 1 && (
              <button type="button" onClick={() => removeVariantRow(i)} style={{ background: "none", border: "none", color: "var(--bd-red-light)" }}>×</button>
            )}
          </div>
        ))}
        <button type="button" onClick={addVariantRow} style={{ fontSize: 12, color: "var(--bd-green-light)", background: "none", border: "none" }}>
          + Add variant
        </button>
      </div>

      {error && <div style={{ color: "var(--bd-red-light)", fontSize: 12 }}>{error}</div>}
      <button className="btn-primary" style={{ borderRadius: 8, padding: "10px 0", fontWeight: 700, fontSize: 13 }}>Create Product</button>
    </form>
  );
}
