import os
import tempfile

from fastapi.testclient import TestClient


db_file = tempfile.NamedTemporaryFile(delete=False)
db_file.close()
os.environ["STOCKFLOW_DATABASE"] = db_file.name
os.environ["STOCKFLOW_DEMO_USERNAME"] = "demo@stockflow.dev"
os.environ["STOCKFLOW_DEMO_PASSWORD"] = "demo1234"
os.environ["STOCKFLOW_DEMO_TOKEN"] = "test-token"

from backend.app.main import app  # noqa: E402


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"username": "demo@stockflow.dev", "password": "demo1234"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_demo_login_and_dashboard() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.get("/dashboard", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total_products"] >= 6
    assert body["low_stock_count"] >= 1
    assert "simulated" in body["simulated_data_notice"].lower()


def test_protected_routes_require_auth() -> None:
    with TestClient(app) as client:
        response = client.get("/products")

    assert response.status_code == 401


def test_product_search_and_low_stock_filter() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        search_response = client.get("/products?search=barcode", headers=headers)
        low_stock_response = client.get("/products?low_stock=true", headers=headers)

    assert search_response.status_code == 200
    assert any("Barcode" in product["name"] for product in search_response.json())
    assert low_stock_response.status_code == 200
    assert all(product["low_stock"] for product in low_stock_response.json())


def test_create_update_and_delete_product() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        payload = {
            "sku": "SKU-TEST-001",
            "name": "Demo Test Product",
            "category": "Testing",
            "supplier_id": 1,
            "quantity": 33,
            "reorder_level": 7,
            "unit_price": 45.5,
            "status": "active",
        }

        create_response = client.post("/products", json=payload, headers=headers)
        assert create_response.status_code == 201
        product = create_response.json()

        update_payload = {**payload, "quantity": 4, "reorder_level": 6}
        update_response = client.put(f"/products/{product['id']}", json=update_payload, headers=headers)
        assert update_response.status_code == 200
        assert update_response.json()["low_stock"] is True

        delete_response = client.delete(f"/products/{product['id']}", headers=headers)
        assert delete_response.status_code == 204


def test_validation_errors_are_reported() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.post(
            "/products",
            json={
                "sku": "x",
                "name": "",
                "category": "Testing",
                "supplier_id": 1,
                "quantity": -1,
                "reorder_level": 0,
                "unit_price": 10,
                "status": "active",
            },
            headers=headers,
        )

    assert response.status_code == 422


def test_create_order() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.post(
            "/orders",
            json={
                "order_number": "SO-TEST-001",
                "product_id": 1,
                "customer_name": "Demo Customer",
                "quantity": 3,
                "status": "pending",
                "order_type": "sales",
            },
            headers=headers,
        )

    assert response.status_code == 201
    assert response.json()["product_name"]
