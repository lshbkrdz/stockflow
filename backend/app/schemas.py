from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    username: EmailStr
    password: str = Field(min_length=4, max_length=80)


class LoginResponse(BaseModel):
    token: str
    user: dict[str, str]
    simulated_data_notice: str


class SupplierCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    contact_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(min_length=5, max_length=40)
    status: Literal["active", "paused"] = "active"


class Supplier(SupplierCreate):
    id: int
    created_at: str


class ProductCreate(BaseModel):
    sku: str = Field(min_length=3, max_length=40)
    name: str = Field(min_length=2, max_length=160)
    category: str = Field(min_length=2, max_length=80)
    supplier_id: int = Field(gt=0)
    quantity: int = Field(ge=0)
    reorder_level: int = Field(ge=0)
    unit_price: float = Field(ge=0)
    status: Literal["active", "archived"] = "active"


class ProductUpdate(ProductCreate):
    pass


class Product(ProductCreate):
    id: int
    supplier_name: str
    low_stock: bool
    created_at: str
    updated_at: str


class OrderCreate(BaseModel):
    order_number: str = Field(min_length=3, max_length=40)
    product_id: int = Field(gt=0)
    customer_name: str = Field(min_length=2, max_length=120)
    quantity: int = Field(gt=0)
    status: Literal["pending", "processing", "shipped", "delivered", "cancelled"]
    order_type: Literal["sales", "purchase"]


class Order(OrderCreate):
    id: int
    product_name: str
    created_at: str


class DashboardStats(BaseModel):
    total_products: int
    total_suppliers: int
    total_orders: int
    low_stock_count: int
    inventory_value: float
    simulated_data_notice: str
