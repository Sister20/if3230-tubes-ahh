from lib.struct.address import Address


class AddressTest:
    def __init__(self):
        self.address = Address("127.0.0.1", 8080)

    def test_address(self):
        assert self.address.ip != ""
        assert self.address.port != 0
        assert self.address.ip == "127.0.0.1"
        assert self.address.port == 8080
        print("Address test passed")

    def str_test(self):
        assert str(self.address) != ""
        assert str(self.address) == "127.0.0.1:8080"
        print("Address str test passed")

    def iter_test(self):
        assert iter(self.address) is not None
        print("Address iter test passed")

    def eq_test(self):
        assert self.address != Address("sacas", 8080)
        assert self.address == Address("127.0.0.1", 8080)
        print("Address eq test passed")
