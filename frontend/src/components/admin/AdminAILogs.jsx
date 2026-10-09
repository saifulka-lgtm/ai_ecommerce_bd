import React, { useEffect, useState } from "react";
import { api } from "../../services/api";

export default function AdminAILogs({ token }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.adminListAILogs(token, 100).then(setLogs).finally(() => setLoading(false));
  }, [token]);

  if (loading) return <div style={{ color: "var(--text-2)" }}>Loading AI activity…</div>;

  return (
    <div>
      <h3 style={{ marginTop: 0 }}>AI Activity Log ({logs.length})</h3>
      <p style={{ color: "var(--text-2)", fontSize: 12, marginTop: -8 }}>
        Every tool the AI agent called, in response to a real customer message — this is what the AI actually did, not what it said.
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {logs.map((log) => (
          <div key={log.id} style={{ background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 10, padding: 12, fontSize: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={{ color: "var(--text-2)" }}>{new Date(log.created_at).toLocaleString()}</span>
              <span
                style={{
                  padding: "2px 8px",
                  borderRadius: 999,
                  fontSize: 10,
                  fontWeight: 700,
                  background: log.success ? "rgba(46,204,113,0.15)" : "rgba(244,42,65,0.15)",
                  color: log.success ? "var(--success)" : "var(--bd-red-light)",
                }}
              >
                {log.success ? "SUCCESS" : "FAILED"}
              </span>
            </div>
            <div style={{ marginBottom: 4 }}>
              <span style={{ color: "var(--text-2)" }}>Customer: </span>
              <span>&ldquo;{log.customer_message}&rdquo;</span>
            </div>
            <div style={{ marginBottom: 4 }}>
              <span style={{ color: "var(--text-2)" }}>AI action: </span>
              <b style={{ color: "var(--bd-green-light)" }}>{log.tool_name}</b>
              {log.execution_time_ms != null && <span style={{ color: "var(--text-2)" }}> ({log.execution_time_ms}ms)</span>}
            </div>
            {Object.keys(log.tool_arguments || {}).length > 0 && (
              <div style={{ color: "var(--text-2)", fontFamily: "monospace", fontSize: 11 }}>
                args: {JSON.stringify(log.tool_arguments)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
