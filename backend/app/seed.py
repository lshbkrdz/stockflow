from .database import execute, fetch_one


SUPPLIERS = [
    ("Northline Supply Co.", "Maya Reed", "maya@northline.example", "+1 555 0141", "active"),
    ("Metro Parts Group", "Daniel Kim", "daniel@metroparts.example", "+1 555 0188", "active"),
    ("Orbit Warehouse Ltd.", "Sofia Reyes", "sofia@orbitwarehouse.example", "+1 555 0199", "active"),
    ("Summit Office Goods", "Alex Morgan", "alex@summitgoods.example", "+1 555 0112", "paused"),
]

PRODUCTS = [
    ("SKU-1001", "USB-C Docking Station", "Electronics", 1, 42, 12, 89.0, "active"),
    ("SKU-1002", "Wireless Barcode Scanner", "Warehouse", 2, 8, 10, 129.0, "active"),
    ("SKU-1003", "Thermal Label Printer", "Warehouse", 2, 17, 6, 214.0, "active"),
    ("SKU-1004", "Standing Desk Frame", "Office", 4, 5, 8, 299.0, "active"),
    ("SKU-1005", "Inventory Tag Roll", "Supplies", 3, 240, 60, 12.5, "active"),
    ("SKU-1006", "Network Switch 24 Port", "Networking", 1, 11, 5, 180.0, "active"),
]

ORDERS = [
    ("SO-7784", 1, "Atlas Retail Demo", 6, "processing", "sales"),
    ("SO-7785", 2, "Northstar Labs Demo", 2, "pending", "sales"),
    ("PO-3091", 4, "Internal Restock Demo", 12, "pending", "purchase"),
    ("SO-7786", 5, "Orbit Services Demo", 50, "shipped", "sales"),
    ("PO-3092", 3, "Internal Restock Demo", 8, "delivered", "purchase"),
]


def seed_demo_data() -> None:
    if fetch_one("SELECT id FROM suppliers LIMIT 1"):
        return

    for supplier in SUPPLIERS:
        execute(
            """
            INSERT INTO suppliers (name, contact_name, email, phone, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            supplier,
        )

    for product in PRODUCTS:
        execute(
            """
            INSERT INTO products (sku, name, category, supplier_id, quantity, reorder_level, unit_price, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            product,
        )

    for order in ORDERS:
        execute(
            """
            INSERT INTO orders (order_number, product_id, customer_name, quantity, status, order_type)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            order,
        )
