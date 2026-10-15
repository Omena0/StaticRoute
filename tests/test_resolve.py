from router.error import is_error
from router.route import Route


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

    def test_resolve_value_non_string(self):
        r = Route("items", {}, "")
        res = r.resolve_value({}, 123)
        assert is_error(res)

    def test_resolve_value_with_dot_notation(self):
        r = Route("items", {}, "")
        args = {"item": {"value": {"name": "test"}}}
        res = r.resolve_value(args, "$item.name")
        assert res == "test"

    def test_resolve_value_dot_notation_on_non_dict(self):
        r = Route("items", {}, "")
        args = {"item": {"value": "notdict"}}
        res = r.resolve_value(args, "$item.name")
        assert is_error(res)

    def test_resolve_value_dot_notation_missing_key(self):
        r = Route("items", {}, "")
        args = {"item": {"value": {}}}
        res = r.resolve_value(args, "$item.name")
        assert is_error(res)

    def test_resolve_value_hash_prefix(self):
        r = Route("items", {}, "")
        res = r.resolve_value({}, "#now")
        assert not is_error(res)

    def test_resolve_new_id_builtin(self):
        r = Route("items", {"type": "get"}, "")
        r.data_store = {"0": {"id": 0}, "1": {"id": 1}}
        res = r.resolve_builtin("new_id")
        assert res == 2

    def test_resolve_new_id_empty_store(self):
        r = Route("items", {"type": "get"}, "")
        r.data_store = {}
        res = r.resolve_builtin("new_id")
        assert res == 0

    def test_resolve_new_id_non_numeric_last_key(self):
        r = Route("items", {"type": "get"}, "")
        r.data_store = {"a": {}}
        res = r.resolve_builtin("new_id")
        assert is_error(res)

    def test_resolve_builtin_identity(self, app):
        from flask import session

        with app.test_request_context():
            session["username"] = "alice"
            r = Route("items", {}, "")
            assert r.resolve_builtin("Identity") == "alice"

    def test_resolve_builtin_session(self, app):
        from flask import session

        with app.test_request_context():
            session["user"] = "bob"
            r = Route("items", {}, "")
            assert r.resolve_builtin("session:user") == "bob"
            assert r.resolve_builtin("session:missing") is None

    def test_resolve_builtin_unknown(self):
        r = Route("items", {}, "")
        res = r.resolve_builtin("unknown")
        assert is_error(res)
