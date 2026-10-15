import os

from router.error import is_error
from router.route import data_store_paths, data_stores, save_data_store


class TestSaveDataStore:
    def test_save_with_unknown_store(self):
        result = save_data_store("nonexistent_store")
        assert is_error(result)

    def test_save_data_store_success(self, temp_stores_dir):
        import json

        # Setup
        store_name = "test.json"
        path = os.path.join(temp_stores_dir, store_name)
        data_stores.clear()
        data_store_paths.clear()
        data_stores["test"] = {"0": {"id": 0, "name": "x"}}
        data_store_paths["test"] = path

        result = save_data_store("test")
        assert result is None
        with open(path) as f:
            loaded = json.load(f)
        assert loaded == {"0": {"id": 0, "name": "x"}}
