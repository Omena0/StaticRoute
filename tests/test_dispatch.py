import json
import os
import tempfile
import time

from flask import Flask

from router.dispatch import (
    dispatch_user_route,
    invalidate_user_cache,
    load_user_routes_manual,
    start_file_watcher,
    stop_file_watcher,
)


class TestDispatch:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.app = Flask(__name__)
        self.app.secret_key = "test"

    def teardown_method(self):
        stop_file_watcher()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_user_routes(self, username: str, routes_config: dict):
        user_dir = os.path.join(self.temp_dir, username)
        os.makedirs(user_dir, exist_ok=True)
        with open(os.path.join(user_dir, "routes.json"), "w") as f:
            json.dump(routes_config, f)

    def _create_data_store(self, username: str, store_name: str, data: dict):
        user_dir = os.path.join(self.temp_dir, username)
        os.makedirs(user_dir, exist_ok=True)
        with open(os.path.join(user_dir, f"{store_name}.json"), "w") as f:
            json.dump(data, f)

    def test_dispatch_user_route_basic_get(self):
        self._create_user_routes("alice", {
            "posts.json": {
                "idx_name": "$post",
                "columns": {"id": "ID", "title": "string", "content": "string"},
                "routes": {
                    "get": {
                        "type": "get",
                        "args": {"$id": {"type": "ID"}},
                        "id": "$id"
                    }
                }
            }
        })
        self._create_data_store("alice", "posts", {
            "0": {"id": 0, "title": "first", "content": "hello"}
        })

        with self.app.test_request_context("/alice/posts/get?id=0"):
            resp = dispatch_user_route("/alice/posts/get", "alice", self.temp_dir)
            assert resp is not None
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["title"] == "first"

    def test_dispatch_user_route_wrong_username(self):
        self._create_user_routes("alice", {
            "posts.json": {
                "routes": {"get": {"type": "get", "args": {"$id": {"type": "ID"}}, "id": "$id"}}
            }
        })

        with self.app.test_request_context("/bob/posts/get?id=0"):
            resp = dispatch_user_route("/bob/posts/get", "alice", self.temp_dir)
            assert resp is None  # Wrong username, returns None to continue catch-all

    def test_dispatch_user_route_nonexistent_store(self):
        self._create_user_routes("alice", {
            "posts.json": {"routes": {"get": {"type": "get", "args": {"$id": {"type": "ID"}}, "id": "$id"}}}
        })

        with self.app.test_request_context("/alice/comments/get?id=0"):
            resp = dispatch_user_route("/alice/comments/get", "alice", self.temp_dir)
            assert resp is None

    def test_dispatch_user_route_nonexistent_route(self):
        self._create_user_routes("alice", {
            "posts.json": {"routes": {"get": {"type": "get", "args": {"$id": {"type": "ID"}}, "id": "$id"}}}
        })

        with self.app.test_request_context("/alice/posts/unknown?id=0"):
            resp = dispatch_user_route("/alice/posts/unknown", "alice", self.temp_dir)
            assert resp is None

    def test_dispatch_user_route_missing_arg(self):
        self._create_user_routes("alice", {
            "posts.json": {
                "routes": {"get": {"type": "get", "args": {"$id": {"type": "ID"}}, "id": "$id"}}
            }
        })

        with self.app.test_request_context("/alice/posts/get"):
            resp = dispatch_user_route("/alice/posts/get", "alice", self.temp_dir)
            assert resp is not None
            assert resp.status_code == 400
            data = resp.get_json()
            assert "Argument not specified" in str(data)

    def test_dispatch_user_route_invalid_type(self):
        self._create_user_routes("alice", {
            "posts.json": {
                "routes": {"get": {"type": "get", "args": {"$id": {"type": "ID"}}, "id": "$id"}}
            }
        })

        with self.app.test_request_context("/alice/posts/get?id=abc"):
            resp = dispatch_user_route("/alice/posts/get", "alice", self.temp_dir)
            assert resp is not None
            assert resp.status_code == 400
            data = resp.get_json()
            assert "Not an ID" in str(data)

    def test_dispatch_user_route_create(self):
        self._create_user_routes("alice", {
            "posts.json": {
                "idx_name": "$post",
                "columns": {"id": "ID", "title": "string", "content": "string", "author": "string"},
                "routes": {
                    "new": {
                        "type": "create",
                        "args": {
                            "title": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "values": {
                            "id": "#new_id",
                            "title": "$title",
                            "content": "$content",
                            "author": "#Identity"
                        }
                    }
                }
            }
        })
        self._create_data_store("alice", "posts", {
            "0": {"id": 0, "title": "first", "content": "hello", "author": "alice"}
        })

        with self.app.test_request_context("/alice/posts/new?title=test&content=hello"):
            from flask import session
            session["username"] = "alice"
            resp = dispatch_user_route("/alice/posts/new", "alice", self.temp_dir)
            assert resp is not None
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["title"] == "test"
            assert data["content"] == "hello"
            assert data["author"] == "alice"

    def test_dispatch_user_route_range(self):
        self._create_user_routes("alice", {
            "posts.json": {
                "routes": {
                    "list": {
                        "type": "range",
                        "args": {
                            "$offset": {"type": "integer", "optional": 0},
                            "$count": {"type": "integer", "optional": 10}
                        },
                        "range": ["$offset", "$count"],
                        "max": 10
                    }
                }
            }
        })
        self._create_data_store("alice", "posts", {
            "0": {"id": 0, "title": "post0"},
            "1": {"id": 1, "title": "post1"},
            "2": {"id": 2, "title": "post2"},
        })

        with self.app.test_request_context("/alice/posts/list?offset=1&count=1"):
            resp = dispatch_user_route("/alice/posts/list", "alice", self.temp_dir)
            assert resp is not None
            assert resp.status_code == 200
            data = resp.get_json()
            assert len(data) == 1
            assert data[0]["title"] == "post1"

    def test_dispatch_user_route_delete(self):
        self._create_user_routes("alice", {
            "posts.json": {
                "idx_name": "$post",
                "routes": {
                    "delete": {
                        "type": "delete",
                        "args": {"$id": {"type": "ID"}},
                        "id": "$id",
                        "require": {"type": "Identity", "value": "$post.author", "error": "Not yours!"}
                    }
                }
            }
        })
        self._create_data_store("alice", "posts", {
            "0": {"id": 0, "title": "first", "content": "hello", "author": "alice"}
        })

        with self.app.test_request_context("/alice/posts/delete?id=0"):
            from flask import session
            session["username"] = "alice"
            resp = dispatch_user_route("/alice/posts/delete", "alice", self.temp_dir)
            assert resp is not None
            assert resp.status_code == 200
            data = resp.get_json()
            assert data == {"result": "ok"}

    def test_dispatch_user_route_delete_forbidden(self):
        self._create_user_routes("alice", {
            "posts.json": {
                "idx_name": "$post",
                "routes": {
                    "delete": {
                        "type": "delete",
                        "args": {"$id": {"type": "ID"}},
                        "id": "$id",
                        "require": {"type": "Identity", "value": "$post.author", "error": "Not yours!"}
                    }
                }
            }
        })
        self._create_data_store("alice", "posts", {
            "0": {"id": 0, "title": "first", "content": "hello", "author": "bob"}
        })

        with self.app.test_request_context("/alice/posts/delete?id=0"):
            from flask import session
            session["username"] = "alice"
            resp = dispatch_user_route("/alice/posts/delete", "alice", self.temp_dir)
            assert resp is not None
            assert resp.status_code == 400
            data = resp.get_json()
            assert "Not yours" in str(data)

    def test_cache_invalidation_on_file_change(self):
        self._create_user_routes("alice", {
            "posts.json": {
                "routes": {"get": {"type": "get", "args": {"$id": {"type": "ID"}}, "id": "$id"}}
            }
        })
        self._create_data_store("alice", "posts", {
            "0": {"id": 0, "title": "first"}
        })

        with self.app.test_request_context("/alice/posts/get?id=0"):
            resp1 = dispatch_user_route("/alice/posts/get", "alice", self.temp_dir)
            assert resp1 is not None

        # Modify routes.json
        time.sleep(0.1)
        self._create_user_routes("alice", {
            "posts.json": {
                "routes": {"get": {"type": "get", "args": {"$id": {"type": "ID"}}, "id": "$id"}}
            }
        })

        with self.app.test_request_context("/alice/posts/get?id=0"):
            resp2 = dispatch_user_route("/alice/posts/get", "alice", self.temp_dir)
            assert resp2 is not None

    def test_invalidate_user_cache(self):
        self._create_user_routes("alice", {
            "posts.json": {
                "routes": {"get": {"type": "get", "args": {"$id": {"type": "ID"}}, "id": "$id"}}
            }
        })
        self._create_data_store("alice", "posts", {"0": {"id": 0, "title": "first"}})

        with self.app.test_request_context("/alice/posts/get?id=0"):
            resp = dispatch_user_route("/alice/posts/get", "alice", self.temp_dir)
            assert resp is not None

        invalidate_user_cache("alice")

        with self.app.test_request_context("/alice/posts/get?id=0"):
            resp = dispatch_user_route("/alice/posts/get", "alice", self.temp_dir)
            assert resp is not None

    def test_load_user_routes_manual(self):
        self._create_user_routes("alice", {
            "posts.json": {
                "routes": {"get": {"type": "get", "args": {"$id": {"type": "ID"}}, "id": "$id"}}
            }
        })

        routes = load_user_routes_manual("alice", self.temp_dir)
        assert routes is not None
        assert "posts.json" in routes

    def test_load_user_routes_manual_nonexistent(self):
        routes = load_user_routes_manual("nonexistent", self.temp_dir)
        assert routes is None

    def test_file_watcher_start_stop(self):
        start_file_watcher(self.temp_dir)
        time.sleep(0.1)
        stop_file_watcher()

    def test_dispatch_with_trailing_slash(self):
        self._create_user_routes("alice", {
            "posts.json": {
                "routes": {"get": {"type": "get", "args": {"$id": {"type": "ID"}}, "id": "$id"}}
            }
        })
        self._create_data_store("alice", "posts", {"0": {"id": 0, "title": "first"}})

        with self.app.test_request_context("/alice/posts/get?id=0"):
            resp = dispatch_user_route("/alice/posts/get/", "alice", self.temp_dir)
            assert resp is not None

    def test_dispatch_path_too_short(self):
        resp = dispatch_user_route("/alice", "alice", self.temp_dir)
        assert resp is None

        resp = dispatch_user_route("/alice/posts", "alice", self.temp_dir)
        assert resp is None
