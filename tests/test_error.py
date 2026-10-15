from router.error import is_error


class TestErrorHandling:
    def test_error_dict_structure(self):
        from router.error import error

        e = error("Something went wrong")
        assert e == {"error": "Something went wrong"}

    def test_is_error_true(self):
        from router.error import error

        assert is_error(error("test"))

    def test_is_error_false(self):

        assert not is_error({"data": "value"})

    def test_is_error_false_plain_string(self):

        assert not is_error("error string")

    def test_is_error_false_multiple_keys(self):

        assert not is_error({"error": "x", "extra": "y"})

    def test_is_error_false_non_string_value(self):

        assert not is_error({"error": 123})

    def test_error_with_empty_string(self):
        from router.error import error

        assert error("") == {"error": ""}
