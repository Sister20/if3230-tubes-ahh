from lib.struct.AppendEntry   import AppendEntry
from lib.struct.address       import Address
from lib.struct.KVStore       import KVStore

import asyncio
from threading     import Thread
from xmlrpc.client import ServerProxy
from typing        import Any, List, Dict
from enum          import Enum
import socket
import json
import time
import aioxmlrpc.client
import random


class RaftNode:
    HEARTBEAT_INTERVAL   = 1
    ELECTION_TIMEOUT_MIN = 3
    ELECTION_TIMEOUT_MAX = 4
    RPC_TIMEOUT          = 0.5

    class NodeType(Enum):
        LEADER    = 1
        CANDIDATE = 2
        FOLLOWER  = 3

    def __init__(self, application : Any, addr: Address, contact_addr: Address = None):
        # ? random float for timeout, called here so in this node, the random float is the same
        random_float = random.uniform(
            RaftNode.ELECTION_TIMEOUT_MIN, RaftNode.ELECTION_TIMEOUT_MAX)
        socket.setdefaulttimeout(RaftNode.RPC_TIMEOUT)
        self.leader_id:           int = -1
        self.address:             Address = addr
        self.type:                RaftNode.NodeType = RaftNode.NodeType.FOLLOWER
        self.log:                 List[int, str,
                                       str, int] = []  # [term, command, args, request_id]
        self.app:                 KVStore =  application

        # Election stuff
        self.election_term:       int = 0
        self.election_timeout:    int = time.time(
        ) + random_float
        self.election_interval:   int = random_float
        self.voted_for:           int = -1
        self.vote_count:          int = 0

        self.commit_index:        int = -1
        self.last_applied:        int = -1
        self.last_heartbeat_received: int = time.time()

        # Reinit after election
        self.match_index:         Dict[str, int] = {}
        self.next_index:          Dict[str, int] = {}

        self.cluster_addr_list:   List[Address] = []
        self.cluster_leader_addr: Address = None

        self.timeout_thread = None
        self.heartbeat_thread = None

        if contact_addr is None:
            self.cluster_addr_list.append(self.address)
            self.__initialize_as_leader()
        else:
            self.__initialize_as_follower()
            self.__try_to_apply_membership(contact_addr)



    # Internal Raft Node methods
    def __print_log(self, text: str):
        print(f"[{self.address}] [{time.strftime('%H:%M:%S')}] {text}")

    def __initialize_as_leader(self):
        self.__print_log("Initialize as leader node...")
        self.cluster_leader_addr = self.address
        self.type                = RaftNode.NodeType.LEADER
        request = {
            "cluster_leader_addr": self.address
        }
        # TODO : Inform to all node this is new leader
            
        self.heartbeat_thread = Thread(target=asyncio.run,args=[self.__leader_heartbeat()])
        self.heartbeat_thread.start()

    def __initialize_as_follower(self):
        self.__print_log("Initialize as follower node...")
        self.type = RaftNode.NodeType.FOLLOWER
        self.election_term = 0

        self.timeout_thread = Thread(target=asyncio.run,args=[self.__election_timeout()])
        self.timeout_thread.start()

    async def __leader_heartbeat(self):
        # TODO : Send periodic heartbeat
        while True:
            self.__print_log("[Leader] Sending heartbeat...")
            for addr in self.cluster_addr_list:
                if Address(addr['ip'], addr['port']) == self.address:
                    continue
                self.append_entries(addr)

            await asyncio.sleep(RaftNode.HEARTBEAT_INTERVAL)
    
    async def __election_timeout(self):
        # TODO : Start election
        while True:
            if time.time() > self.election_timeout and self.type == RaftNode.NodeType.FOLLOWER:
                self.__print_log("Election timeout")
                self.election_term += 1
                self._reset_election_timeout()
                self.type = RaftNode.NodeType.CANDIDATE
                self.voted_for = self.address
                self.vote_count = 1

                self.__print_log(f"Starting election for term {self.election_term}")
                


            await asyncio.sleep(self.election_interval)
    
    def _reset_election_timeout(self):
        random_float =  random.uniform( RaftNode.ELECTION_TIMEOUT_MIN, RaftNode.ELECTION_TIMEOUT_MAX)
        self.election_timeout = time.time() + random_float
        self.election_interval = random_float

    def append_entries(self, follower_addr: Address):
        self.last_heartbeat_received = time.time()

        prev_log_index = len(self.log) - 1
        prev_log_term = 0

        if len(self.log) > 0:
            prev_log_term = self.log[prev_log_index][0]

        request = {
            "term": self.election_term,
            "leader_addr": self.address,
            "prev_log_index": prev_log_index,
            "prev_log_term": prev_log_term,
            "entries": self.log,
            "leader_commit": self.commit_index,
            "cluster_addr_list": self.cluster_addr_list,
        }

        if not isinstance(follower_addr, Address):
            follower_addr = Address(follower_addr['ip'], follower_addr['port'])

        index = self.next_index[str(follower_addr)] if str(
            follower_addr) in self.next_index else 0

        if (prev_log_index >= index):
            request["entries"] = self.log[index+1:]
            self.__print_log(
                f"Sending append_entries to {follower_addr} with entries {request['entries']}")

            response = self.__send_request(
                request, "append_entry", follower_addr)

            if(not self.next_index.get(str(follower_addr))):
              self.next_index[str(follower_addr)] = -1
            
            if(not self.match_index.get(str(follower_addr))) :
              self.match_index[str(follower_addr)] = -1

            if (response["success"] == False):
                if (self.next_index[str(follower_addr)] > 0):
                    self.next_index[str(follower_addr)] -= 1
            else:
                self.match_index[str(follower_addr)] = prev_log_index
                self.next_index[str(follower_addr)] = prev_log_index

        else:
            response = self.__send_request(
                request, "append_entry", follower_addr)

        return response

    def __try_to_apply_membership(self, contact_addr: Address):
        redirected_addr = contact_addr
        response = {
            "status": "redirected",
            "address": {
                "ip":   contact_addr.ip,
                "port": contact_addr.port,
            }
        }
        print("Applying for membership...")
        redirected_addr = Address(response["address"]["ip"], response["address"]["port"])
        while response.get("status") != "success":
            response        = self.__send_request(self.address, "apply_membership", redirected_addr)
        self.log                 = response["log"]
        self.cluster_addr_list   = response["cluster_addr_list"]
        self.cluster_leader_addr = redirected_addr

    def __send_request(self, request: Any, rpc_name: str, addr: Address) -> "json":
        if not isinstance(addr, Address):
            addr = Address(addr["ip"], addr["port"])

        node = ServerProxy(f"http://{addr.ip}:{addr.port}")
        json_request = json.dumps(request)
        rpc_function = getattr(node, rpc_name)
        response = {
            "success": False,
        }
        try:
            response = json.loads(rpc_function(json_request))
            self.__print_log(response)
        except KeyboardInterrupt:
            exit(1)
        except ConnectionRefusedError:
            self.__print_log(f"[{addr}] is not replying (refused, likely down)")    
        except:
            self.__print_log(f"[{addr}] is not replying (nack)")

        return response

    # Inter-node RPCs
    def heartbeat(self, json_request: str) -> "json":
        # TODO : Implement heartbeat
        response = {
            "heartbeat_response": "ack",
            "address":            self.address,
        }
        return json.dumps(response)


    # Client RPCs
    def execute(self, json_request: str) -> "json":
        request = json.loads(json_request)
        # TODO : Implement execute
        return json.dumps(request)