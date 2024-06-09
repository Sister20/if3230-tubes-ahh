from lib.struct.AppendEntry import AppendEntry
from lib.struct.address import Address


class AppendEntryTest:
    def __init__(self):
        self.appnd = AppendEntry()
        self.leader_addr = Address("127.0.0.1", 5001)
        self.appnd_req = self.appnd.Request(1, 0, 0, 0, [], 0)
        self.appnd_res = self.appnd.Response(1, True)

    def test_append_entry_request(self):
        assert self.appnd_req.term == 1
        assert self.appnd_req.leader_addr == 0
        assert self.appnd_req.prev_log_index == 0
        assert self.appnd_req.prev_log_term == 0
        assert self.appnd_req.entries == []
        assert self.appnd_req.leader_commit_index == 0
        print("Append entry request test passed")

    def test_append_entry_response(self):
        assert self.appnd_res.term == 1
        assert self.appnd_res.success == True
        print("Append entry response test passed")

    def test_append_entry_request_dict(self):
        assert self.appnd_req.to_dict() == {
            "term": 1,
            "leader_addr": {
                "ip": "127.0.0.1",
                "port": 5001,
            },
            "prev_log_index": 0,
            "prev_log_term": 0,
            "entries": [],
            "leader_commit_index": 0,
        }

