# Import structs
from lib.struct.address import Address

# Import libraries
from typing import List

class AppendEntry:
    pass

    class Request:
        def __init__(self, term, leader_addr, prev_log_index, prev_log_term, entries, leader_commit_index) -> None:
            self.term: int = term
            self.leader_addr: Address = leader_addr
            self.prev_log_index: int = prev_log_index
            self.prev_log_term: int = prev_log_term
            self.entries: List[str] = entries
            self.leader_commit_index: int = leader_commit_index

        def to_dict(self) -> dict:
            return {
                "term": self.term,
                "leader_addr": {
                    "ip": self.leader_addr.ip,
                    "port": self.leader_addr.port
                },
                "prev_log_index": self.prev_log_index,
                "prev_log_term": self.prev_log_term,
                "entries": self.entries,
                "leader_commit_index": self.leader_commit_index}

    class Response:
        def __init__(self, term, success) -> None:
            self.term: int = term
            self.success: bool = success

        def to_dict(self) -> dict:
            return {"term": self.term,
                    "success": self.success}
