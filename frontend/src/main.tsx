import { type FormEvent, useEffect, useState } from "react";
import { Boxes, CircleDollarSign, ClipboardList, LayoutDashboard, LogOut, Package, ReceiptText, Users } from "lucide-react";
import "./styles.css";

type Summary = { organization: string; customers: number; suppliers: number; items: number; orders: number; invoices: number; outstanding_amount: string };
const api = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("luma_token");
  const response = await fetch(`${api}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(options.headers ?? {}) },
  });
  if (!response.ok) throw new Error((await response.json()).detail ?? "Request failed");
  return response.json();
}

function Login({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState("demo@luma.local");
  const [password, setPassword] = useState("demo-password");
  const [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await request("/api/v1/demo/seed", { method: "POST" });
      const result = await request<{ access_token: string }>("/api/v1/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      localStorage.setItem("luma_token", result.access_token);
      onLogin();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to sign in"); }
  }
  return <main className="login"><div className="login-card"><div className="brand-mark">L</div><p className="eyebrow">LUMA ERP</p><h1>Run the business clearly.</h1><p className="muted">Sales, inventory, purchasing, and finance in one calm workspace.</p><form onSubmit={submit}><label>Email<input value={email} onChange={event => setEmail(event.target.value)} /></label><label>Password<input type="password" value={password} onChange={event => setPassword(event.target.value)} /></label>{error && <p className="error">{error}</p>}<button>Open demo workspace</button></form></div></main>;
}

function Dashboard({ onLogout }: { onLogout: () => void }) {
  const [summary, setSummary] = useState<Summary | null>(null);
  useEffect(() => { request<Summary>("/api/v1/dashboard/summary").then(setSummary).catch(onLogout); }, [onLogout]);
  const cards = summary ? [["Customers", summary.customers, Users], ["Items", summary.items, Package], ["Orders", summary.orders, ClipboardList], ["Invoices", summary.invoices, ReceiptText]] as const : [];
  return <div className="app-shell"><aside><div className="side-brand"><span className="brand-mark small">L</span><strong>Luma</strong></div><nav><a className="active"><LayoutDashboard size={18} />Overview</a><a><Users size={18} />Customers</a><a><Boxes size={18} />Inventory</a><a><CircleDollarSign size={18} />Finance</a></nav><button className="logout" onClick={onLogout}><LogOut size={17} />Sign out</button></aside><main className="dashboard"><header><div><p className="eyebrow">WORKSPACE</p><h1>{summary?.organization ?? "Loading workspace..."}</h1></div><div className="status-dot">● Live demo</div></header><section className="hero"><div><p className="eyebrow">OPERATIONS OVERVIEW</p><h2>Good morning. Here is your business at a glance.</h2><p className="muted">A focused command center for the daily order-to-cash and procure-to-pay cycle.</p></div><button className="secondary">View reports</button></section><section className="metrics">{cards.map(([label, value, Icon]) => <article className="metric" key={label}><div className="icon-wrap"><Icon size={19} /></div><p className="muted">{label}</p><strong>{value}</strong><small>Across your workspace</small></article>)}<article className="metric highlight"><div className="icon-wrap"><CircleDollarSign size={19} /></div><p className="muted">Outstanding</p><strong>${summary?.outstanding_amount ?? "0.00"}</strong><small>Receivables to follow up</small></article></section><section className="lower"><article className="panel"><div className="panel-title"><div><p className="eyebrow">QUICK START</p><h3>Move from idea to action</h3></div></div><div className="quick-grid"><button><ClipboardList size={18} /><span>Create sales order<small>Start an order-to-cash flow</small></span></button><button><Package size={18} /><span>Check inventory<small>Review items and stock</small></span></button><button><ReceiptText size={18} /><span>Review invoices<small>Track billing and payments</small></span></button></div></article><article className="panel insight"><p className="eyebrow">PRODUCT NOTE</p><h3>Designed for growing teams</h3><p className="muted">Luma keeps operational detail connected to financial visibility, so teams can act without switching between disconnected tools.</p></article></section></main></div>;
}

export default function App() {
  const [loggedIn, setLoggedIn] = useState(Boolean(localStorage.getItem("luma_token")));
  if (!loggedIn) return <Login onLogin={() => setLoggedIn(true)} />;
  return <Dashboard onLogout={() => { localStorage.removeItem("luma_token"); setLoggedIn(false); }} />;
}
