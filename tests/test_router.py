import json
import os
import shutil
import tempfile

import pytest

from router.error import is_error
from router.load import load_data_stores
from router.route import Route, data_store_paths, data_stores


@pytest.fixture
def temp_stores_dir():
    d = tempfile.mkdtemp(prefix="route_tests_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def routes_config():
    return {
        "items.json": {
            "idx_name": "$item",
            "routes": {
                "list": {
                    "type": "range",
                    "args": {
                        "$offset": {"type": "integer", "optional": 0},
                        "$count": {"type": "integer", "optional": 50},
                    },
                    "range": ["$offset", "$count"],
                    "max": 50,
                    "max_error": "You can only request up to 50 items.",
                    "select": "*",
                },
                "get": {"type": "get", "args": {"$id": {"type": "ID"}}, "id": "$id"},
                "new": {
                    "type": "create",
                    "args": {
                        "name": {
                            "type": "content",
                            "validator": {"type": "length", "max_value": 100, "error": "name too long"},
                        },
                        "value": {"type": "content"},
                    },
                    "values": {"id": "#new_id", "name": "$name", "value": "$value"},
                },
                "delete": {"type": "delete", "args": {"$id": {"type": "ID"}}, "id": "$id", "error": "Item not found."},
            },
        }
    }


@pytest.fixture
def app(temp_stores_dir, routes_config):
    import flask

    data_stores.clear()
    data_store_paths.clear()

    # Seed the items store with test data
    seed_data = {
        "0": {"id": 0, "name": "first", "value": "hello"},
        "1": {"id": 1, "name": "second", "value": "world"},
    }
    seed_path = os.path.join(temp_stores_dir, "items.json")
    with open(seed_path, "w") as f:
        json.dump(seed_data, f)

    app = flask.Flask(__name__)
    app.secret_key = "test-secret"

    load_data_stores(app, temp_stores_dir, routes_config)

    return app


class TestTypeValidation:
    def test_string(self):
        r = Route("items", {}, "")
        valid, _ = r.validate_type("string", "hello")
        assert valid

    def test_not_string(self):
        r = Route("items", {}, "")
        valid, _ = r.validate_type("string", 123)
        assert not valid

    def test_integer(self):
        r = Route("items", {}, "")
        valid, _ = r.validate_type("integer", 42)
        assert valid

    def test_not_integer(self):
        r = Route("items", {}, "")
        valid, _ = r.validate_type("integer", 3.14)
        assert not valid

    def test_id(self):
        r = Route("items", {}, "")
        valid, _ = r.validate_type("ID", 5)
        assert valid

    def test_not_id(self):
        r = Route("items", {}, "")
        valid, _ = r.validate_type("ID", -1)
        assert not valid


class TestResolveType:
    def test_resolve_string(self):
        r = Route("items", {}, "")
        assert r.resolve_type({"type": "string", "value": "hello"}) == "hello"

    def test_resolve_int_from_str(self):
        r = Route("items", {}, "")
        result = r.resolve_type({"type": "integer", "value": "42"})
        assert result == 42

    def test_resolve_int_from_number(self):
        r = Route("items", {}, "")
        result = r.resolve_type({"type": "integer", "value": 42})
        assert result == 42

    def test_resolve_float(self):
        r = Route("items", {}, "")
        result = r.resolve_type({"type": "number", "value": "3.14"})
        assert result == 3.14

    def test_resolve_type_missing_value(self):
        r = Route("items", {}, "")
        assert is_error(r.resolve_type({"type": "string"}))


class TestResolveValue:
    def test_dollar_arg(self):
        r = Route("items", {}, "")
        args = {"name": {"type": "content", "value": "hello"}}
        assert r.resolve_value(args, "$name") == "hello"

    def test_plain_string(self):
        r = Route("items", {}, "")
        assert r.resolve_value({}, "static") == "static"

    def test_undefined_arg(self):
        r = Route("items", {}, "")
        result = r.resolve_value({}, "$undefined")
        assert is_error(result)

    def test_now_builtin(self):
        r = Route("items", {}, "")
        result = r.resolve_value({}, "#now")
        assert not is_error(result)
        assert isinstance(result, float)


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


class TestErrorHandling:
    def test_error_dict_structure(self):
        from router.error import error

        e = error("Something went wrong")
        assert e == {"error": "Something went wrong"}

    def test_is_error_true(self):
        from router.error import error, is_error

        assert is_error(error("test"))

    def test_is_error_false(self):
        from router.error import is_error

        assert not is_error({"data": "value"})

    def test_is_error_false_plain_string(self):
        from router.error import is_error

        assert not is_error("error string")


class TestSaveDataStore:
    def test_save_with_unknown_store(self):
        from router.route import save_data_store

        result = save_data_store("nonexistent_store")
        assert is_error(result)
