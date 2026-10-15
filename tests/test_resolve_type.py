from router.error import is_error
from router.route import Route


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

    def test_resolve_negative_number(self):
        r = Route("items", {}, "")
        result = r.resolve_type({"type": "integer", "value": "-5"})
        assert result == -5

    def test_resolve_negative_float(self):
        r = Route("items", {}, "")
        result = r.resolve_type({"type": "number", "value": "-3.14"})
        assert result == -3.14

    def test_resolve_number_from_int(self):
        r = Route("items", {}, "")
        assert r.resolve_type({"type": "number", "value": 7}) == 7
        assert r.resolve_type({"type": "ID", "value": 5}) == 5

    def test_resolve_content(self):
        r = Route("items", {}, "")
        assert r.resolve_type({"type": "content", "value": "hi"}) == "hi"

    def test_resolve_non_dict(self):
        r = Route("items", {}, "")
        assert r.resolve_type("plain") == "plain"
        assert r.resolve_type(123) == 123

    def test_resolve_missing_type_key(self):
        r = Route("items", {}, "")
        assert r.resolve_type({"value": "x"}) == {"value": "x"}

    def test_resolve_bad_number_string(self):
        r = Route("items", {}, "")
        res = r.resolve_type({"type": "number", "value": "abc"})
        assert is_error(res)

    def test_resolve_bad_number_type(self):
        r = Route("items", {}, "")
        res = r.resolve_type({"type": "number", "value": []})
        assert is_error(res)

    def test_resolve_unknown_type(self):
        r = Route("items", {}, "")
        res = r.resolve_type({"type": "unknown", "value": "x"})
        assert is_error(res)

    def test_resolve_string_coerces_non_str(self):
        r = Route("items", {}, "")
        assert r.resolve_type({"type": "string", "value": 5}) == "5"

    def test_resolve_multiple_dots_rejected(self):
        """Only a single '.' is accepted for a float."""
        r = Route("items", {}, "")
        res = r.resolve_type({"type": "number", "value": "1.2.3"})
        assert is_error(res)
