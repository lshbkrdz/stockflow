import React, { FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { api } from "./api";
import type { DashboardStats, Order, Product, ProductPayload, Supplier } from "./types";
import "./styles.css";

const emptyProduct: ProductPayload = {
  sku: "",
  name: "",
  category: "",
  supplier_id: 1,
  quantity: 0,
  reorder_level: 5,
  unit_price: 0,
  status: "active"
};

function App() {
  const [token, setToken] = useState(localStorage.getItem(api.tokenKey));
  const [loginError, setLoginError] = useState("");
  const [loading, setLoading] = useState(false);
  const [busyMessage, setBusyMessage] = useState("");
  const [error, setError] = useState("");
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [lowStock, setLowStock] = useState<boolean | null>(null);
  const [form, setForm] = useState<ProductPayload>(emptyProduct);
  const [editingId, setEditingId] = useState<number | null>(null);

  const selectedSupplier = suppliers[0]?.id ?? 1;

  useEffect(() => {
    if (!token) return;
    void loadData();
  }, [token]);

  useEffect(() => {
    if (!token) return;
    const timeout = window.setTimeout(() => void loadProducts(), 250);
    return () => window.clearTimeout(timeout);
  }, [search, category, lowStock, token]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoginError("");
    setLoading(true);
    const formData = new FormData(event.currentTarget);

    try {
      const response = await api.login(String(formData.get("username")), String(formData.get("password")));
      localStorage.setItem(api.tokenKey, response.token);
      setToken(response.token);
    } catch (err) {
      setLoginError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const [dashboardData, supplierData, orderData, categoryData] = await Promise.all([
        api.dashboard(),
        api.suppliers(),
        api.orders(),
        api.categories()
      ]);
      setStats(dashboardData);
      setSuppliers(supplierData);
      setOrders(orderData);
      setCategories(categoryData.categories);
      setForm((current) => ({ ...current, supplier_id: current.supplier_id || supplierData[0]?.id || 1 }));
      await loadProducts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load StockFlow data.");
    } finally {
      setLoading(false);
    }
  }

  async function loadProducts() {
    try {
      const productData = await api.products({ search, category, lowStock });
      setProducts(productData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load products.");
    }
  }

  async function handleProductSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusyMessage(editingId ? "Updating product..." : "Adding product...");
    setError("");

    try {
      if (editingId) {
        await api.updateProduct(editingId, form);
      } else {
        await api.createProduct(form);
      }
      setForm({ ...emptyProduct, supplier_id: selectedSupplier });
      setEditingId(null);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Product save failed.");
    } finally {
      setBusyMessage("");
    }
  }

  async function handleDelete(product: Product) {
    const confirmed = window.confirm(`Delete ${product.name}? Products linked to orders cannot be deleted.`);
    if (!confirmed) return;

    setBusyMessage("Deleting product...");
    setError("");
    try {
      await api.deleteProduct(product.id);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Product delete failed.");
    } finally {
      setBusyMessage("");
    }
  }

  function startEdit(product: Product) {
    setEditingId(product.id);
    setForm({
      sku: product.sku,
      name: product.name,
      category: product.category,
      supplier_id: product.supplier_id,
      quantity: product.quantity,
      reorder_level: product.reorder_level,
      unit_price: product.unit_price,
      status: product.status
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function logout() {
    localStorage.removeItem(api.tokenKey);
    setToken(null);
  }

  const lowStockProducts = useMemo(() => products.filter((product) => product.low_stock), [products]);

  if (!token) {
    return <LoginScreen loading={loading} error={loginError} onLogin={handleLogin} />;
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span>SF</span>
          <div>
            <strong>StockFlow</strong>
            <small>Inventory Operations</small>
          </div>
        </div>
        <nav>
          <a href="#dashboard">Dashboard</a>
          <a href="#products">Products</a>
          <a href="#suppliers">Suppliers</a>
          <a href="#orders">Orders</a>
        </nav>
        <button className="ghost-button" onClick={logout}>Log out</button>
      </aside>

      <section className="content">
        <header className="topbar" id="dashboard">
          <div>
            <p className="eyebrow">Demo Application</p>
            <h1>StockFlow Inventory Management</h1>
            <p>Manage products, supplier records, stock quantities, low-stock warnings, and demo orders from one responsive dashboard.</p>
          </div>
          <div className="demo-notice">{stats?.simulated_data_notice || "This application uses simulated demo data only."}</div>
        </header>

        {error && <div className="alert error">{error}</div>}
        {busyMessage && <div className="alert busy">{busyMessage}</div>}
        {loading && <div className="loading-card">Loading StockFlow data...</div>}

        <section className="stats-grid">
          <Stat label="Products" value={stats?.total_products ?? 0} />
          <Stat label="Suppliers" value={stats?.total_suppliers ?? 0} />
          <Stat label="Orders" value={stats?.total_orders ?? 0} />
          <Stat label="Low stock" value={stats?.low_stock_count ?? 0} warning />
          <Stat label="Inventory value" value={`$${(stats?.inventory_value ?? 0).toLocaleString()}`} />
        </section>

        <section className="workspace-grid">
          <ProductForm
            form={form}
            suppliers={suppliers}
            editingId={editingId}
            onChange={setForm}
            onSubmit={handleProductSubmit}
            onCancel={() => {
              setEditingId(null);
              setForm({ ...emptyProduct, supplier_id: selectedSupplier });
            }}
          />

          <section className="panel">
            <div className="panel-head">
              <div>
                <p className="eyebrow">Low-stock warnings</p>
                <h2>Action queue</h2>
              </div>
              <span className="badge warning">{lowStockProducts.length} alerts</span>
            </div>
            {lowStockProducts.length === 0 ? (
              <EmptyState title="No low-stock alerts" text="All visible products are above their reorder level." />
            ) : (
              <div className="alert-list">
                {lowStockProducts.map((product) => (
                  <article key={product.id}>
                    <strong>{product.name}</strong>
                    <span>{product.quantity} in stock, reorder at {product.reorder_level}</span>
                  </article>
                ))}
              </div>
            )}
          </section>
        </section>

        <section className="panel" id="products">
          <div className="panel-head panel-head-wide">
            <div>
              <p className="eyebrow">Products</p>
              <h2>Inventory list</h2>
            </div>
            <div className="filters">
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search SKU, product, supplier" />
              <select value={category} onChange={(event) => setCategory(event.target.value)}>
                <option value="">All categories</option>
                {categories.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
              <select value={lowStock === null ? "" : String(lowStock)} onChange={(event) => setLowStock(event.target.value === "" ? null : event.target.value === "true")}>
                <option value="">All stock</option>
                <option value="true">Low stock only</option>
                <option value="false">Healthy stock</option>
              </select>
            </div>
          </div>
          <ProductTable products={products} onEdit={startEdit} onDelete={handleDelete} />
        </section>

        <section className="two-column">
          <SupplierPanel suppliers={suppliers} />
          <OrderPanel orders={orders} />
        </section>
      </section>
    </main>
  );
}

function LoginScreen({ loading, error, onLogin }: { loading: boolean; error: string; onLogin: (event: FormEvent<HTMLFormElement>) => void }) {
  return (
    <main className="login-page">
      <form className="login-card" onSubmit={onLogin}>
        <p className="eyebrow">StockFlow Demo</p>
        <h1>Inventory and order management</h1>
        <p>Use the seeded demo credentials to explore the working API, dashboard, products, suppliers, and orders.</p>
        <label>
          Email
          <input name="username" type="email" defaultValue="demo@stockflow.dev" required />
        </label>
        <label>
          Password
          <input name="password" type="password" defaultValue="demo1234" required />
        </label>
        {error && <div className="alert error">{error}</div>}
        <button className="primary-button" disabled={loading}>{loading ? "Signing in..." : "Sign in to demo"}</button>
        <span className="demo-notice">All records are fake seeded demo data.</span>
      </form>
    </main>
  );
}

function Stat({ label, value, warning = false }: { label: string; value: number | string; warning?: boolean }) {
  return (
    <article className="stat-card">
      <span>{label}</span>
      <strong className={warning ? "warning-text" : ""}>{value}</strong>
    </article>
  );
}

function ProductForm(props: {
  form: ProductPayload;
  suppliers: Supplier[];
  editingId: number | null;
  onChange: (product: ProductPayload) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onCancel: () => void;
}) {
  const { form, suppliers, editingId, onChange, onSubmit, onCancel } = props;
  const setField = <K extends keyof ProductPayload>(field: K, value: ProductPayload[K]) => onChange({ ...form, [field]: value });

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">{editingId ? "Edit product" : "Add product"}</p>
          <h2>{editingId ? "Update inventory item" : "New inventory item"}</h2>
        </div>
      </div>
      <form className="product-form" onSubmit={onSubmit}>
        <label>SKU<input value={form.sku} onChange={(event) => setField("sku", event.target.value)} required minLength={3} /></label>
        <label>Name<input value={form.name} onChange={(event) => setField("name", event.target.value)} required /></label>
        <label>Category<input value={form.category} onChange={(event) => setField("category", event.target.value)} required /></label>
        <label>Supplier
          <select value={form.supplier_id} onChange={(event) => setField("supplier_id", Number(event.target.value))}>
            {suppliers.map((supplier) => <option key={supplier.id} value={supplier.id}>{supplier.name}</option>)}
          </select>
        </label>
        <label>Quantity<input type="number" min={0} value={form.quantity} onChange={(event) => setField("quantity", Number(event.target.value))} required /></label>
        <label>Reorder level<input type="number" min={0} value={form.reorder_level} onChange={(event) => setField("reorder_level", Number(event.target.value))} required /></label>
        <label>Unit price<input type="number" min={0} step="0.01" value={form.unit_price} onChange={(event) => setField("unit_price", Number(event.target.value))} required /></label>
        <label>Status
          <select value={form.status} onChange={(event) => setField("status", event.target.value as ProductPayload["status"])}>
            <option value="active">Active</option>
            <option value="archived">Archived</option>
          </select>
        </label>
        <div className="form-actions">
          <button className="primary-button">{editingId ? "Save changes" : "Add product"}</button>
          {editingId && <button className="ghost-button" type="button" onClick={onCancel}>Cancel</button>}
        </div>
      </form>
    </section>
  );
}

function ProductTable({ products, onEdit, onDelete }: { products: Product[]; onEdit: (product: Product) => void; onDelete: (product: Product) => void }) {
  if (products.length === 0) {
    return <EmptyState title="No products found" text="Try clearing search filters or add a new product." />;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Product</th>
            <th>Supplier</th>
            <th>Qty</th>
            <th>Reorder</th>
            <th>Price</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {products.map((product) => (
            <tr key={product.id}>
              <td><strong>{product.name}</strong><span>{product.sku} / {product.category}</span></td>
              <td>{product.supplier_name}</td>
              <td>{product.quantity}</td>
              <td>{product.reorder_level}</td>
              <td>${product.unit_price.toFixed(2)}</td>
              <td><span className={`badge ${product.low_stock ? "warning" : "ok"}`}>{product.low_stock ? "Low stock" : product.status}</span></td>
              <td className="row-actions">
                <button onClick={() => onEdit(product)}>Edit</button>
                <button onClick={() => onDelete(product)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SupplierPanel({ suppliers }: { suppliers: Supplier[] }) {
  return (
    <section className="panel" id="suppliers">
      <div className="panel-head"><div><p className="eyebrow">Suppliers</p><h2>Supplier list</h2></div></div>
      {suppliers.length === 0 ? <EmptyState title="No suppliers" text="Seed data did not load yet." /> : (
        <div className="stack-list">
          {suppliers.map((supplier) => (
            <article key={supplier.id}>
              <strong>{supplier.name}</strong>
              <span>{supplier.contact_name} / {supplier.email}</span>
              <b className={`badge ${supplier.status === "active" ? "ok" : "muted"}`}>{supplier.status}</b>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function OrderPanel({ orders }: { orders: Order[] }) {
  return (
    <section className="panel" id="orders">
      <div className="panel-head"><div><p className="eyebrow">Orders</p><h2>Recent orders</h2></div></div>
      {orders.length === 0 ? <EmptyState title="No orders" text="Seed data did not load yet." /> : (
        <div className="stack-list">
          {orders.map((order) => (
            <article key={order.id}>
              <strong>{order.order_number} / {order.product_name}</strong>
              <span>{order.customer_name} ordered {order.quantity} units</span>
              <b className={`badge ${order.order_type === "sales" ? "ok" : "warning"}`}>{order.status}</b>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <p>{text}</p>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
