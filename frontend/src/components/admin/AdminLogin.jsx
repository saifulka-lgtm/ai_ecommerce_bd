import React, { useState } from "react";
import { api } from "../../services/api";

export default function AdminLogin({ onLoggedIn }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.adminLogin(username, password);
      onLoggedIn(res.access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <form
        onSubmit={submit}
        style={{
          background: "var(--bg-1)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          padding: 32,
          width: 340,
          display: "flex",
          flexDirection: "column",
          gap: 14,
          boxShadow: "var(--shadow)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 8 }}>
          <div style={{ fontSize: 28 }}>🛠️</div>
          <h2 style={{ margin: "8px 0 0", fontSize: 18 }}>Admin Login</h2>
          <p style={{ color: "var(--text-2)", fontSize: 12 }}>Fashion BD — Store Management</p>
        </div>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          style={inputStyle}
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          style={inputStyle}
        />
        {error && <div style={{ color: "var(--bd-red-light)", fontSize: 12 }}>{error}</div>}
        <button className="btn-primary" disabled={loading} style={{ borderRadius: 8, padding: "10px 0", fontWeight: 700, fontSize: 14 }}>
          {loading ? "Signing in…" : "Sign In"}
        </button>
      </form>
    </div>
  );
}

const inputStyle = {
  background: "var(--bg-3)",
  border: "1px solid var(--border)",
  color: "var(--text-0)",
  borderRadius: 8,
  padding: "10px 12px",
  fontSize: 13,
};
