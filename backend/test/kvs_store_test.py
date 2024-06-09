from lib.struct.KVStore import KVStore


class KVSStoreTest:
    def __init__(self):
        self.kv = KVStore()

    def test_append_entry(self):
        self.kv.put("key", "value")
        self.kv.append("key", "value")
        assert self.kv.get("key") == "valuevalue"
        print("Append entry test passed")

    def test_append_entry_empty(self):
        self.kv.put("key", "")
        self.kv.append("key", "value")
        assert self.kv.get("key") == "value"
        print("Append entry empty test passed")

    def test_append_entry_nonexistent(self):
        self.kv.append("key", "value")
        assert self.kv.get("keys") == ""
        print("Append entry nonexistent test passed")

    def test_append_entry_empty_value(self):
        self.kv.put("key", "value")
        self.kv.append("key", "")
        assert self.kv.get("key") == "value"
        print("Append entry empty value test passed")

    def test_append_entry_empty_key(self):
        self.kv.put("", "value")
        self.kv.append("", "value")
        assert self.kv.get("") == "valuevalue"
        print("Append entry empty key test passed")

    def test_append_entry_empty_key_value(self):
        self.kv.put("", "")
        self.kv.append("", "")
        assert self.kv.get("") == ""
        print("Append entry empty key value test passed")

    def test_get_keys(self):
        self.kv.put("key", "value")
        assert "key" in self.kv.get_keys()
        print("Get keys test passed")

    def test_get_values(self):
        self.kv.put("key", "value")
        assert "value" in self.kv.get_values()
        print("Get values test passed")

    def test_get_items(self):
        self.kv.put("key", "value")
        assert ("key", "value") in self.kv.get_items()
        print("Get items test passed")

    def test_clear(self):
        self.kv.put("key", "value")
        self.kv.clear()
        assert self.kv.get("key") == ""
        print("Clear test passed")

    def test_delete(self):
        self.kv.put("key", "value")
        self.kv.delete("key")
        assert self.kv.get("key") == ""
        print("Delete test passed")

    def test_strln(self):
        self.kv.put("key", "value")
        assert self.kv.strln("key") == "5"
        print("Strln test passed")

    def test_get_all(self):
        self.kv.put("key", "value")
        assert self.kv.get_all() == {"key": "value"}
        print("Get all test passed")

    def test_get_nonexistent(self):
        assert self.kv.get("key") == ""
        print("Get nonexistent test passed")