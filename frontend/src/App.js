import { useState, useEffect } from "react";

const API = "http://localhost:8000/api/payments/";

const Badge = ({ type }) => {
  const styles = {
    card:      { background: "#dbeafe", color: "#1e40af" },
    cash:      { background: "#dcfce7", color: "#166534" },
    completed: { background: "#dcfce7", color: "#166534" },
    pending:   { background: "#fef9c3", color: "#854d0e" },
    failed:    { background: "#fee2e2", color: "#991b1b" },
    refunded:  { background: "#f3e8ff", color: "#6b21a8" },
  };
  const s = styles[type] || { background: "#f1f5f9", color: "#475569" };
  return (
    <span style={{
      ...s, padding: "2px 10px", borderRadius: 99,
      fontSize: 12, fontWeight: 600, textTransform: "capitalize"
    }}>
      {type}
    </span>
  );
};

const Modal = ({ payment, onClose, onSave }) => {
  const [form, setForm] = useState({ ...payment });
  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async () => {
    await fetch(`${API}${payment.id}/`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, user_id: form.user?.id }),
    });
    onSave();
    onClose();
  };

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.45)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 999
    }}>
      <div style={{
        background: "#fff", borderRadius: 16, padding: 32,
        width: 480, boxShadow: "0 20px 60px rgba(0,0,0,0.2)"
      }}>
        <h2 style={{ margin: "0 0 20px", fontSize: 20, color: "#1e293b" }}>Edit Payment #{payment.id}</h2>

        {[
          { label: "Amount", name: "amount", type: "number" },
          { label: "Currency", name: "currency" },
          { label: "Description", name: "description" },
        ].map(f => (
          <div key={f.name} style={{ marginBottom: 14 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#64748b", marginBottom: 4 }}>
              {f.label}
            </label>
            <input
              name={f.name}
              type={f.type || "text"}
              value={form[f.name] || ""}
              onChange={handleChange}
              style={{
                width: "100%", padding: "8px 12px", borderRadius: 8,
                border: "1.5px solid #e2e8f0", fontSize: 14,
                outline: "none", boxSizing: "border-box"
              }}
            />
          </div>
        ))}

        <div style={{ marginBottom: 14 }}>
          <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#64748b", marginBottom: 4 }}>
            Status
          </label>
          <select
            name="status"
            value={form.status}
            onChange={handleChange}
            style={{
              width: "100%", padding: "8px 12px", borderRadius: 8,
              border: "1.5px solid #e2e8f0", fontSize: 14
            }}
          >
            {["pending", "completed", "failed", "refunded"].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 24 }}>
          <button onClick={onClose} style={{
            padding: "9px 20px", borderRadius: 8, border: "1.5px solid #e2e8f0",
            background: "#fff", cursor: "pointer", fontSize: 14
          }}>Cancel</button>
          <button onClick={handleSubmit} style={{
            padding: "9px 20px", borderRadius: 8, border: "none",
            background: "#2563eb", color: "#fff", cursor: "pointer", fontSize: 14, fontWeight: 600
          }}>Save Changes</button>
        </div>
      </div>
    </div>
  );
};

export default function App() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [editing, setEditing]   = useState(null);
  const [filter, setFilter]     = useState("all");
  const [msg, setMsg]           = useState("");

  const fetchPayments = async () => {
    setLoading(true);
    try {
      const res  = await fetch(API);
      const json = await res.json();
      setPayments(json.data || []);
    } catch {
      setMsg("Could not connect to backend. Make sure Django is running on port 8000.");
    }
    setLoading(false);
  };

  useEffect(() => { fetchPayments(); }, []);

  const handleDelete = async (id) => {
    if (!window.confirm(`Delete payment #${id}?`)) return;
    await fetch(`${API}${id}/`, { method: "DELETE" });
    setMsg(`Payment #${id} deleted.`);
    fetchPayments();
  };

  const displayed = filter === "all"
    ? payments
    : payments.filter(p => p.payment_type === filter);

  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc", fontFamily: "system-ui, sans-serif" }}>

      {/* Header */}
      <div style={{
        background: "#fff", borderBottom: "1px solid #e2e8f0",
        padding: "0 40px", display: "flex", alignItems: "center",
        justifyContent: "space-between", height: 64
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: "#2563eb", display: "flex", alignItems: "center", justifyContent: "center"
          }}>
            <span style={{ color: "#fff", fontSize: 16 }}>💳</span>
          </div>
          <span style={{ fontWeight: 700, fontSize: 18, color: "#1e293b" }}>Payment Module</span>
        </div>
        <span style={{ fontSize: 13, color: "#94a3b8" }}>Django + React Demo</span>
      </div>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "32px 24px" }}>

        {/* Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16, marginBottom: 28 }}>
          {[
            { label: "Total Payments", value: payments.length, color: "#2563eb" },
            { label: "Card", value: payments.filter(p => p.payment_type === "card").length, color: "#7c3aed" },
            { label: "Cash", value: payments.filter(p => p.payment_type === "cash").length, color: "#059669" },
            { label: "Completed", value: payments.filter(p => p.status === "completed").length, color: "#d97706" },
          ].map(s => (
            <div key={s.label} style={{
              background: "#fff", borderRadius: 12, padding: "20px 24px",
              border: "1px solid #e2e8f0"
            }}>
              <div style={{ fontSize: 28, fontWeight: 700, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 13, color: "#94a3b8", marginTop: 2 }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Filter + message */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <div style={{ display: "flex", gap: 8 }}>
            {["all", "card", "cash"].map(f => (
              <button key={f} onClick={() => setFilter(f)} style={{
                padding: "6px 18px", borderRadius: 99, fontSize: 13, fontWeight: 600,
                border: "1.5px solid",
                borderColor: filter === f ? "#2563eb" : "#e2e8f0",
                background: filter === f ? "#2563eb" : "#fff",
                color: filter === f ? "#fff" : "#64748b",
                cursor: "pointer", textTransform: "capitalize"
              }}>{f}</button>
            ))}
          </div>
          {msg && <span style={{ fontSize: 13, color: "#059669", fontWeight: 500 }}>{msg}</span>}
        </div>

        {/* Table */}
        <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#f8fafc" }}>
                {["ID", "User", "Amount", "Type", "Status", "Date", "Actions"].map(h => (
                  <th key={h} style={{
                    padding: "12px 16px", textAlign: "left",
                    fontSize: 12, fontWeight: 600, color: "#94a3b8",
                    borderBottom: "1px solid #e2e8f0", textTransform: "uppercase", letterSpacing: "0.05em"
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} style={{ padding: 40, textAlign: "center", color: "#94a3b8" }}>Loading...</td></tr>
              ) : displayed.length === 0 ? (
                <tr><td colSpan={7} style={{ padding: 40, textAlign: "center", color: "#94a3b8" }}>
                  No payments found. Add one via Postman → POST /api/payments/
                </td></tr>
              ) : displayed.map((p, i) => (
                <tr key={p.id} style={{ borderBottom: i < displayed.length - 1 ? "1px solid #f1f5f9" : "none" }}>
                  <td style={{ padding: "14px 16px", fontSize: 13, color: "#94a3b8" }}>#{p.id}</td>
                  <td style={{ padding: "14px 16px" }}>
                    <div style={{ fontWeight: 600, fontSize: 14, color: "#1e293b" }}>{p.user?.name || "—"}</div>
                    <div style={{ fontSize: 12, color: "#94a3b8" }}>{p.user?.email}</div>
                  </td>
                  <td style={{ padding: "14px 16px", fontWeight: 700, fontSize: 15, color: "#1e293b" }}>
                    {p.amount} <span style={{ fontSize: 12, color: "#94a3b8" }}>{p.currency}</span>
                  </td>
                  <td style={{ padding: "14px 16px" }}><Badge type={p.payment_type} /></td>
                  <td style={{ padding: "14px 16px" }}><Badge type={p.status} /></td>
                  <td style={{ padding: "14px 16px", fontSize: 13, color: "#64748b" }}>
                    {new Date(p.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding: "14px 16px" }}>
                    <div style={{ display: "flex", gap: 8 }}>
                      <button onClick={() => setEditing(p)} style={{
                        padding: "5px 14px", borderRadius: 6, fontSize: 12, fontWeight: 600,
                        border: "1.5px solid #e2e8f0", background: "#fff",
                        color: "#2563eb", cursor: "pointer"
                      }}>Edit</button>
                      <button onClick={() => handleDelete(p.id)} style={{
                        padding: "5px 14px", borderRadius: 6, fontSize: 12, fontWeight: 600,
                        border: "1.5px solid #fee2e2", background: "#fff",
                        color: "#dc2626", cursor: "pointer"
                      }}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer note */}
        <div style={{ marginTop: 20, fontSize: 13, color: "#94a3b8", textAlign: "center" }}>
          Backend: <code style={{ background: "#f1f5f9", padding: "2px 6px", borderRadius: 4 }}>
            localhost:8000/api/payments/
          </code> &nbsp;|&nbsp; Test with Postman &nbsp;|&nbsp; Django + MySQL + React
        </div>
      </div>

      {editing && (
        <Modal payment={editing} onClose={() => setEditing(null)} onSave={fetchPayments} />
      )}
    </div>
  );
}