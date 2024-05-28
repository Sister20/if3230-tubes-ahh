from lib.struct.address import Address

class KVStore:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def put(self, key, value):
        self.store[key] = value
    
    def append(self, key, value):
        self.store[key] += value

    def strln(self):
        return str(self.store)

    def delete(self, key):
        del self.store[key]

    def get_all(self):
        return self.store

    def get_keys(self):
        return self.store.keys()

    def get_values(self):
        return self.store.values()

    def get_items(self):
        return self.store.items()

    def clear(self):
        self.store.clear()