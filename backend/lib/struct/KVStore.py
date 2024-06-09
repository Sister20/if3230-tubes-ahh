# Import structs
from lib.struct.address import Address

class KVStore:
    def __init__(self):
        self.store = {}

    # Get the value of a key
    def get(self, key):
        if key not in self.store:
            return ""
        return self.store.get(key)

    # Set the value of a key
    def put(self, key, value):
        self.store[key] = value
    
    # Append the value to a key
    def append(self, key, value):
        if key not in self.store:
            self.store[key] = value
        else:
            self.store[key] += value
            

    # Get the length of the value of a key
    def strln(self, key):
        if key not in self.store:
            return str(0)
        return str(len(self.store[key]))

    # Delete a key
    def delete(self, key):
        del self.store[key]

    # Get all the key-value pairs
    def get_all(self):
        return self.store

    # Get all the keys
    def get_keys(self):
        return self.store.keys()

    # Get all the values
    def get_values(self):
        return self.store.values()

    # Get all the items
    def get_items(self):
        return self.store.items()

    # Clear the store
    def clear(self):
        self.store.clear()