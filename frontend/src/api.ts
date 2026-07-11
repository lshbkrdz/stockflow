import type { DashboardStats, Order, Product, ProductPayload, Supplier } from "./types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const TOKEN_KEY = "stockflow_demo_token";

type LoginResponse = {
  token: string;
  user: { email: string; role: string };
  simulated_data_notice: string;
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem(TOKEN_KEY);
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers
    }
  });

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    try {
      const body = await response.json();
      message = Array.isArray(body.detail)
        ? body.detail.map((item: { msg: string }) => item.msg).join(", ")
        : body.detail || message;
    } catch {
      // Keep the fallback message when the API does not return JSON.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  tokenKey: TOKEN_KEY,
  login(username: string, password: string) {
    return request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password })
    });
  },
  dashboard() {
    return request<DashboardStats>("/dashboard");
  },
  suppliers() {
    return request<Supplier[]>("/suppliers");
  },
  products(filters: { search?: string; category?: string; lowStock?: boolean | null }) {
    const params = new URLSearchParams();
    if (filters.search) params.set("search", filters.search);
    if (filters.category) params.set("category", filters.category);
    if (filters.lowStock !== null && filters.lowStock !== undefined) params.set("low_stock", String(filters.lowStock));
    return request<Product[]>(`/products?${params.toString()}`);
  },
  categories() {
    return request<{ categories: string[] }>("/meta/categories");
  },
  createProduct(payload: ProductPayload) {
    return request<Product>("/products", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  updateProduct(productId: number, payload: ProductPayload) {
    return request<Product>(`/products/${productId}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },
  deleteProduct(productId: number) {
    return request<void>(`/products/${productId}`, { method: "DELETE" });
  },
  orders() {
    return request<Order[]>("/orders");
  }
};
