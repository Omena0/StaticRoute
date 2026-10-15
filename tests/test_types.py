from router.route import Route


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

    def test_id_negative_zero_and_non_numeric(self):
        r = Route("items", {}, "")
        valid, _ = r.validate_type("ID", -1)
        assert not valid
        valid, _ = r.validate_type("ID", "5")
        assert valid
        valid, _ = r.validate_type("ID", "abc")
        assert not valid

    def test_number(self):
        r = Route("items", {}, "")
        assert r.validate_type("number", 3)[0]
        assert r.validate_type("number", "3.14")[0]
        assert r.validate_type("number", "-1")[0]
        assert not r.validate_type("number", "abc")[0]

    def test_content(self):
        r = Route("items", {}, "")
        assert r.validate_type("content", "hello")[0]
        assert r.validate_type("content", "hello\nworld")[0]  # newline allowed in string
        assert r.validate_type("content", "test")[0]

    def test_unknown_type(self):
        r = Route("items", {}, "")
        valid, msg = r.validate_type("unknown", "x")
        assert not valid
        assert "NotImplemented" in msg

    def test_dict_type_spec(self):
        r = Route("items", {}, "")
        valid, _ = r.validate_type({"type": "string"}, "hi")
        assert valid
