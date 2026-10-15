import json
import os
import shutil
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from router.route import data_store_paths, data_stores


@pytest.fixture(autouse=True)
def _clean_registries():
    """Isolate the module-level store registries for every test."""
    data_stores.clear()
    data_store_paths.clear()
    yield
    data_stores.clear()
    data_store_paths.clear()


@pytest.fixture
def temp_stores_dir():
    d = tempfile.mkdtemp(prefix="route_tests_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def seed_file(temp_stores_dir):
    """Write a store file into the temp stores dir and return its path."""

    def _seed(store_name, contents):
        path = os.path.join(temp_stores_dir, store_name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(contents, f)
        return path

    return _seed


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
def make_app(temp_stores_dir, seed_file):
    """Build a Flask app with ``routes``; returns ``(app, load_result)``."""

    def _make(routes, seed=None):
        import flask

        from router.load import load_data_stores

        data_stores.clear()
        data_store_paths.clear()

        for store_name, contents in (seed or {}).items():
            seed_file(store_name, contents)

        app = flask.Flask("make_app_test")
        app.secret_key = "test-secret"

        result = load_data_stores(app, temp_stores_dir, routes)
        return app, result

    return _make


@pytest.fixture
def saved_store(seed_file):
    """Register an ``items`` store that persists to a file in the temp dir.

    Returns the path of the store file; the in-memory registry is cleared by
    the autouse ``_clean_registries`` fixture afterwards.
    """
    from router.route import data_stores

    store = {"0": {"id": 0, "name": "first"}, "1": {"id": 1, "name": "second"}}
    path = seed_file("items.json", store)
    data_stores["items"] = store
    data_store_paths["items"] = path
    return path


@pytest.fixture
def app(temp_stores_dir, routes_config, seed_file):
    import flask

    from router.load import load_data_stores

    data_stores.clear()
    data_store_paths.clear()

    # Seed the items store with test data
    seed_file(
        "items.json",
        {
            "0": {"id": 0, "name": "first", "value": "hello"},
            "1": {"id": 1, "name": "second", "value": "world"},
        },
    )

    app = flask.Flask(__name__)
    app.secret_key = "test-secret"

    load_data_stores(app, temp_stores_dir, routes_config)

    return app
