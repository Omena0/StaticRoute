from router.error import error, is_error
from router.route import Route, data_stores


def _arg(value, type_="string"):
    if isinstance(value, bool):
        type_ = "string"
    elif isinstance(value, int):
        type_ = "integer"
    elif isinstance(value, float):
        type_ = "number"
    else:
        type_ = "string"
    return {"value": value, "type": type_}


def _args(**kwargs):
    return {name: _arg(value) for name, value in kwargs.items()}


class TestGetRoute:
    def setup_method(self):
        data_stores["items"] = {
            "0": {"id": 0, "name": "first", "value": "hello"},
            "1": {"id": 1, "name": "second", "value": "world"},
        }

    def test_get_existing(self):
        r = Route("items", {"type": "get", "id": "$id"}, "")
        assert r.get_return(_args(id="0")) == {"id": 0, "name": "first", "value": "hello"}

    def test_get_last_row(self):
        r = Route("items", {"type": "get", "id": "$id"}, "")
        assert r.get_return(_args(id="1")) == {"id": 1, "name": "second", "value": "world"}

    def test_get_missing(self):
        r = Route("items", {"type": "get", "id": "$id"}, "")
        assert r.get_return(_args(id="999")) == error("Not found: 999")

    def test_get_without_id_config(self):
        r = Route("items", {"type": "get"}, "")
        assert r.get_return(_args(id="0")) == error("InvalidRoute: No get ID specified.")

    def test_get_unresolvable_id(self):
        r = Route("items", {"type": "get", "id": "$id"}, "")
        assert is_error(r.get_return({}))

    def test_get_int_id_matches_str_key(self):
        r = Route("items", {"type": "get", "id": "$id"}, "")
        assert r.get_return({"id": _arg(0, "integer")}) == {"id": 0, "name": "first", "value": "hello"}

    def test_get_unmatched_id_type(self):
        r = Route("items", {"type": "get", "id": "#now"}, "")
        assert is_error(r.get_return({}))

    def test_get_idx_name_injected(self):
        r = Route("items", {"type": "get", "id": "$id"}, "item")
        out = r.get_return(_args(id="0"))
        assert out == {"id": 0, "name": "first", "value": "hello"}
        assert r.idx_name == "item"
