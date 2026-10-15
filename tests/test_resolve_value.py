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
        args = {"item": {"name": "test"}}
        res = r.resolve_value(args, "$item.name")
        assert res == "test"

    def test_resolve_value_dot_notation_on_non_dict(self):
        r = Route("items", {}, "")
        args = {"item": "notdict"}
        res = r.resolve_value(args, "$item.name")
        assert is_error(res)

    def test_resolve_value_dot_notation_missing_key(self):
        r = Route("items", {}, "")
        args = {"item": {}}
        res = r.resolve_value(args, "$item.name")
        assert is_error(res)

    def test_resolve_value_dot_notation_erases_prefix(self):
        """The leading '$' is stripped before splitting on '.'."""
        r = Route("items", {}, "")
        res = r.resolve_value({}, "$a.b")
        assert is_error(res)
        assert "NotDefinedError" in res["error"]

    def test_resolve_value_hash_prefix(self):
        r = Route("items", {}, "")
        res = r.resolve_value({}, "#now")
        assert not is_error(res)

    def test_resolve_value_number_coercion(self):
        r = Route("items", {}, "")
        args = {"count": {"type": "integer", "value": "3"}}
        assert r.resolve_value(args, "$count") == 3

    def test_resolve_value_unimplemented_builtin(self):
        r = Route("items", {}, "")
        res = r.resolve_value({}, "#nope")
        assert is_error(res)

    def test_resolve_value_empty_string(self):
        r = Route("items", {}, "")
        assert r.resolve_value({}, "") == ""

    def test_resolve_value_index_name_row(self):
        """The idx_name is injected into args by get_return, so it resolves as a row."""
        r = Route("items", {"type": "get", "id": "$id"}, "item")
        args = {"id": {"value": "0", "type": "ID"}, "item": {"id": 0, "name": "first"}}
        assert r.resolve_value(args, "$item.name") == "first"
