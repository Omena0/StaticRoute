import json
import os
import shutil
import tempfile

import pytest

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
