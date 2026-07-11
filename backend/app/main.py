from contextlib import asynccontextmanager
from typing import Annotated, AsyncIterator

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import execute, fetch_all, fetch_one, get_connection, initialize_database
from .schemas import (
    DashboardStats,
    LoginRequest,
    LoginResponse,
    Order,
    OrderCreate,
    Product,
    ProductCreate,
    ProductUpdate,
    Supplier,
)
from .seed import seed_demo_data


SIMULATED_NOTICE = "StockFlow uses simulated seeded demo data for portfolio evaluation. Do not treat records as real client data."


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    seed_demo_data()
    yield


app = FastAPI(
    title="StockFlow API",
    description="Inventory and order management demo API with simulated data.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_demo_auth(authorization: Annotated[str | None, Header()] = None) -> dict[str, str]:
    expected = f"Bearer {settings.demo_token}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid demo token required. Log in with the demo credentials first.",
        )
    return {"email": settings.demo_username, "role": "Demo Admin"}


def product_query(where: str = "", params: tuple = ()) -> list[dict]:
    return fetch_all(
        f"""
        SELECT
            products.*,
            suppliers.name AS supplier_name,
            CASE WHEN products.quantity <= products.reorder_level THEN 1 ELSE 0 END AS low_stock
        FROM products
        JOIN suppliers ON suppliers.id = products.supplier_id
        {where}
        ORDER BY products.updated_at DESC, products.id DESC
        """,
        params,
    )


def order_query(where: str = "", params: tuple = ()) -> list[dict]:
    return fetch_all(
        f"""
        SELECT
            orders.*,
            products.name AS product_name
        FROM orders
        JOIN products ON products.id = orders.product_id
        {where}
        ORDER BY orders.created_at DESC, orders.id DESC
        """,
        params,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "stockflow-api"}


@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    if payload.username != settings.demo_username or payload.password != settings.demo_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid demo credentials.")

    return LoginResponse(
        token=settings.demo_token,
        user={"email": settings.demo_username, "role": "Demo Admin"},
        simulated_data_notice=SIMULATED_NOTICE,
    )


@app.get("/dashboard", response_model=DashboardStats)
def dashboard(_: Annotated[dict[str, str], Depends(require_demo_auth)]) -> DashboardStats:
    stats = fetch_one(
        """
        SELECT
            COUNT(*) AS total_products,
            COALESCE(SUM(quantity * unit_price), 0) AS inventory_value,
            SUM(CASE WHEN quantity <= reorder_level THEN 1 ELSE 0 END) AS low_stock_count
        FROM products
        """
    )
    supplier_count = fetch_one("SELECT COUNT(*) AS total_suppliers FROM suppliers")
    order_count = fetch_one("SELECT COUNT(*) AS total_orders FROM orders")

    return DashboardStats(
        total_products=stats["total_products"],
        total_suppliers=supplier_count["total_suppliers"],
        total_orders=order_count["total_orders"],
        low_stock_count=stats["low_stock_count"] or 0,
        inventory_value=round(float(stats["inventory_value"] or 0), 2),
        simulated_data_notice=SIMULATED_NOTICE,
    )


@app.get("/suppliers", response_model=list[Supplier])
def list_suppliers(_: Annotated[dict[str, str], Depends(require_demo_auth)]) -> list[dict]:
    return fetch_all("SELECT * FROM suppliers ORDER BY name ASC")


@app.get("/products", response_model=list[Product])
def list_products(
    _: Annotated[dict[str, str], Depends(require_demo_auth)],
    search: str = "",
    category: str = "",
    low_stock: bool | None = Query(default=None),
) -> list[dict]:
    clauses: list[str] = []
    params: list[str | int] = []

    if search:
        clauses.append("(products.name LIKE ? OR products.sku LIKE ? OR suppliers.name LIKE ?)")
        term = f"%{search}%"
        params.extend([term, term, term])

    if category:
        clauses.append("products.category = ?")
        params.append(category)

    if low_stock is not None:
        clauses.append("products.quantity <= products.reorder_level" if low_stock else "products.quantity > products.reorder_level")

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return product_query(where, tuple(params))


@app.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    _: Annotated[dict[str, str], Depends(require_demo_auth)],
) -> dict:
    if not fetch_one("SELECT id FROM suppliers WHERE id = ?", (payload.supplier_id,)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Supplier does not exist.")

    try:
        product_id = execute(
            """
            INSERT INTO products (sku, name, category, supplier_id, quantity, reorder_level, unit_price, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.sku,
                payload.name,
                payload.category,
                payload.supplier_id,
                payload.quantity,
                payload.reorder_level,
                payload.unit_price,
                payload.status,
            ),
        )
    except Exception as exc:
        if "UNIQUE" in str(exc):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists.") from exc
        raise

    return product_query("WHERE products.id = ?", (product_id,))[0]


@app.put("/products/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    _: Annotated[dict[str, str], Depends(require_demo_auth)],
) -> dict:
    if not fetch_one("SELECT id FROM products WHERE id = ?", (product_id,)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    if not fetch_one("SELECT id FROM suppliers WHERE id = ?", (payload.supplier_id,)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Supplier does not exist.")

    try:
        execute(
            """
            UPDATE products
            SET sku = ?, name = ?, category = ?, supplier_id = ?, quantity = ?, reorder_level = ?,
                unit_price = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                payload.sku,
                payload.name,
                payload.category,
                payload.supplier_id,
                payload.quantity,
                payload.reorder_level,
                payload.unit_price,
                payload.status,
                product_id,
            ),
        )
    except Exception as exc:
        if "UNIQUE" in str(exc):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists.") from exc
        raise

    return product_query("WHERE products.id = ?", (product_id,))[0]


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    _: Annotated[dict[str, str], Depends(require_demo_auth)],
) -> None:
    if not fetch_one("SELECT id FROM products WHERE id = ?", (product_id,)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    if fetch_one("SELECT id FROM orders WHERE product_id = ? LIMIT 1", (product_id,)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete a product linked to orders.")

    execute("DELETE FROM products WHERE id = ?", (product_id,))


@app.get("/orders", response_model=list[Order])
def list_orders(
    _: Annotated[dict[str, str], Depends(require_demo_auth)],
    status_filter: str = "",
) -> list[dict]:
    if status_filter:
        return order_query("WHERE orders.status = ?", (status_filter,))
    return order_query()


@app.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    _: Annotated[dict[str, str], Depends(require_demo_auth)],
) -> dict:
    if not fetch_one("SELECT id FROM products WHERE id = ?", (payload.product_id,)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product does not exist.")

    try:
        order_id = execute(
            """
            INSERT INTO orders (order_number, product_id, customer_name, quantity, status, order_type)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload.order_number,
                payload.product_id,
                payload.customer_name,
                payload.quantity,
                payload.status,
                payload.order_type,
            ),
        )
    except Exception as exc:
        if "UNIQUE" in str(exc):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order number already exists.") from exc
        raise

    return order_query("WHERE orders.id = ?", (order_id,))[0]


@app.get("/meta/categories")
def categories(_: Annotated[dict[str, str], Depends(require_demo_auth)]) -> dict[str, list[str]]:
    rows = fetch_all("SELECT DISTINCT category FROM products ORDER BY category ASC")
    return {"categories": [row["category"] for row in rows]}


@app.post("/admin/reset-demo-data")
def reset_demo_data(_: Annotated[dict[str, str], Depends(require_demo_auth)]) -> dict[str, str]:
    with get_connection() as connection:
        connection.executescript("DELETE FROM orders; DELETE FROM products; DELETE FROM suppliers;")
        connection.commit()
    seed_demo_data()
    return {"status": "reset", "simulated_data_notice": SIMULATED_NOTICE}
