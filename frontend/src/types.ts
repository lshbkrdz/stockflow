export type Supplier = {
  id: number;
  name: string;
  contact_name: string;
  email: string;
  phone: string;
  status: "active" | "paused";
  created_at: string;
};

export type Product = {
  id: number;
  sku: string;
  name: string;
  category: string;
  supplier_id: number;
  supplier_name: string;
  quantity: number;
  reorder_level: number;
  unit_price: number;
  status: "active" | "archived";
  low_stock: boolean;
  created_at: string;
  updated_at: string;
};

export type ProductPayload = {
  sku: string;
  name: string;
  category: string;
  supplier_id: number;
  quantity: number;
  reorder_level: number;
  unit_price: number;
  status: "active" | "archived";
};

export type Order = {
  id: number;
  order_number: string;
  product_id: number;
  product_name: string;
  customer_name: string;
  quantity: number;
  status: "pending" | "processing" | "shipped" | "delivered" | "cancelled";
  order_type: "sales" | "purchase";
  created_at: string;
};

export type DashboardStats = {
  total_products: number;
  total_suppliers: number;
  total_orders: number;
  low_stock_count: number;
  inventory_value: number;
  simulated_data_notice: string;
};
