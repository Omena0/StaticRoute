import json
import os

from router.error import is_error


class TestRouteOperations:
    def test_get_existing_item(self, app):
        client = app.test_client()
        resp = client.get("/items/get?id=0")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["name"] == "first"

    def test_get_nonexistent_item(self, app):
        client = app.test_client()
        resp = client.get("/items/get?id=999")
        data = resp.get_json()
        assert is_error(data)

    def test_list_items(self, app):
        client = app.test_client()
        resp = client.get("/items/list")
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_list_with_offset_count(self, app):
        client = app.test_client()
        resp = client.get("/items/list?offset=1&count=1")
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "second"

    def test_create_item(self, app):
        client = app.test_client()
        resp = client.get("/items/new?name=test&value=hello")
        data = resp.get_json()
        assert not is_error(data)
        assert data["name"] == "test"
        assert data["value"] == "hello"

    def test_create_item_persists(self, app, temp_stores_dir):
        client = app.test_client()
        resp = client.get("/items/new?name=test&value=hello")
        data = resp.get_json()
        assert not is_error(data)

        new_id = data["id"]
        resp2 = client.get(f"/items/get?id={new_id}")
        data2 = resp2.get_json()
        assert data2["name"] == "test"
        assert data2["value"] == "hello"

    def test_create_item_persists_to_disk(self, app, temp_stores_dir):
        client = app.test_client()
        client.get("/items/new?name=disktest&value=hello")

        with open(os.path.join(temp_stores_dir, "items.json")) as f:
            contents = json.load(f)
        assert "2" in contents
        assert contents["2"]["name"] == "disktest"

    def test_delete_item(self, app):
        client = app.test_client()
        resp = client.get("/items/delete?id=0")
        data = resp.get_json()
        assert data == {"result": "ok"}

    def test_delete_nonexistent(self, app):
        client = app.test_client()
        resp = client.get("/items/delete?id=999")
        data = resp.get_json()
        assert is_error(data)

    def test_missing_arg(self, app):
        client = app.test_client()
        resp = client.get("/items/new?name=test")
        data = resp.get_json()
        assert is_error(data)

    def test_range_validation(self, app):
        client = app.test_client()
        resp = client.get("/items/list?count=99999")
        data = resp.get_json()
        assert is_error(data)

    def test_range_negative_offset(self, app):
        client = app.test_client()
        resp = client.get("/items/list?offset=-1")
        data = resp.get_json()
        assert is_error(data)

    def test_range_negative_count(self, app):
        client = app.test_client()
        resp = client.get("/items/list?count=-1")
        data = resp.get_json()
        assert is_error(data)

    def test_range_with_zero_count(self, app):
        client = app.test_client()
        resp = client.get("/items/list?count=0")
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_create_then_delete_flow(self, app):
        client = app.test_client()
        resp = client.get("/items/new?name=temp&value=data")
        assert not is_error(resp.get_json())
        new_id = resp.get_json()["id"]
        resp = client.get(f"/items/delete?id={new_id}")
        assert resp.get_json() == {"result": "ok"}
        resp = client.get(f"/items/get?id={new_id}")
        assert is_error(resp.get_json())
