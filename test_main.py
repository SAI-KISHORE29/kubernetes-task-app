from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == "Order Service is running as expected."

def test_create_order():
    payload = {"customer": "Sai Kishore", "items": ["Laptop", "Monitor"]}
    response = client.post("/orders", json=payload)
    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["customer"] == "Sai Kishore"