from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

# We patch the logger BEFORE importing the app
with patch("logger.loki_handler"):
    from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    # Match the string from your main.py
    assert response.json() == "Order Service is running as expected."

def test_create_order_validation():
    # Test that invalid payload returns 422 (FastAPI default for validation)
    response = client.post("/orders", json={"customer": "Sai"})
    assert response.status_code == 422