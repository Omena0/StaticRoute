from router.error import is_error
from router.route import Route, data_stores


class TestBuiltinNow:
    def test_now_returns_float(self):
        r = Route("items", {}, "")
        assert isinstance(r.resolve_builtin("now"), float)

    def test_now_advances(self):
        import time

        r = Route("items", {}, "")
        before = time.time()
        assert r.resolve_builtin("now") >= before


class TestBuiltinNewId:
    def test_new_id_increments_last_key(self):
        data_stores["items"] = {"0": {"id": 0}, "1": {"id": 1}}
        r = Route("items", {}, "")
        assert r.resolve_builtin("new_id") == 2

    def test_new_id_empty_store(self):
        data_stores["items"] = {}
        r = Route("items", {}, "")
        assert r.resolve_builtin("new_id") == 0

    def test_new_id_non_numeric_last_key(self):
        data_stores["items"] = {"a": {}}
        r = Route("items", {}, "")
        assert is_error(r.resolve_builtin("new_id"))

    def test_new_id_after_gap(self):
        data_stores["items"] = {"4": {"id": 4}, "7": {"id": 7}}
        r = Route("items", {}, "")
        assert r.resolve_builtin("new_id") == 8

    def test_new_id_unloaded_store_aborts(self, app):
        import pytest
        from werkzeug.exceptions import HTTPException

        r = Route("missing", {}, "")
        with app.test_request_context():
            with pytest.raises(HTTPException):
                r.resolve_builtin("new_id")


class TestBuiltinIdentity:
    def test_identity_returns_username(self, app):
        from flask import session

        with app.test_request_context():
            session["username"] = "alice"
            assert Route("items", {}, "").resolve_builtin("Identity") == "alice"

    def test_identity_anonymous(self, app):
        with app.test_request_context():
            assert Route("items", {}, "").resolve_builtin("Identity") is None


class TestBuiltinSession:
    def test_session_key(self, app):
        from flask import session

        with app.test_request_context():
            session["user"] = "bob"
            assert Route("items", {}, "").resolve_builtin("session:user") == "bob"

    def test_session_missing_key(self, app):
        with app.test_request_context():
            assert Route("items", {}, "").resolve_builtin("session:missing") is None

    def test_session_key_with_colons(self, app):
        from flask import session

        with app.test_request_context():
            session["a:b"] = "c"
            assert Route("items", {}, "").resolve_builtin("session:a:b") == "c"


class TestBuiltinUnimplemented:
    def test_unknown_builtin(self):
        r = Route("items", {}, "")
        res = r.resolve_builtin("unknown")
        assert is_error(res)
        assert "NotImplemented" in res["error"]

    def test_resolve_value_dispatch_to_builtin(self):
        r = Route("items", {}, "")
        assert is_error(r.resolve_value({}, "#unknown"))
