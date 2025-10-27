from fastapi.testclient import TestClient
import pytest
from main import app, items_db, Item

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_db():
    items_db.clear()
    yield
    items_db.clear()

def test_get_items_empty():
    response = client.get("/items")
    assert response.status_code == 200
    assert response.json() == []

def test_create_item_success():
    data = {"id": 1, "name": "Item 1", "description": "A sample item"}
    response = client.post("/items", json=data)
    assert response.status_code == 201
    json_resp = response.json()
    assert json_resp["id"] == data["id"]
    assert json_resp["name"] == data["name"]
    assert json_resp["description"] == data["description"]

    # Make sure item is saved in db
    assert len(items_db) == 1
    assert items_db[0].id == data["id"]

def test_create_item_duplicate_id():
    data = {"id": 1, "name": "Item 1", "description": "A sample item"}
    response1 = client.post("/items", json=data)
    assert response1.status_code == 201

    response2 = client.post("/items", json=data)
    assert response2.status_code == 400
    assert response2.json() == {"detail": "Item with this ID already exists"}

def test_create_item_missing_name():
    data = {"id": 2, "description": "No name provided"}
    response = client.post("/items", json=data)
    assert response.status_code == 422  # validation error

def test_create_item_invalid_id():
    data = {"id": 0, "name": "Invalid ID", "description": "id must be > 0"}
    response = client.post("/items", json=data)
    assert response.status_code == 422  # validation error

def test_create_item_description_too_long():
    long_description = "d" * 301
    data = {"id": 3, "name": "Item 3", "description": long_description}
    response = client.post("/items", json=data)
    assert response.status_code == 422  # validation error

def test_get_items_after_adding():
    data1 = {"id": 1, "name": "Item 1", "description": "desc1"}
    data2 = {"id": 2, "name": "Item 2", "description": "desc2"}

    client.post("/items", json=data1)
    client.post("/items", json=data2)

    response = client.get("/items")
    assert response.status_code == 200
    json_list = response.json()
    assert len(json_list) == 2
    assert json_list[0]["id"] == 1
    assert json_list[1]["id"] == 2
