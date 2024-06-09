# Import structs
from lib.struct.AppendEntry   import AppendEntry
from lib.struct.address       import Address
from lib.struct.KVStore       import KVStore

# Import libraries
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
    # Timeout and interval constants
    HEARTBEAT_INTERVAL   = 1
    ELECTION_TIMEOUT_MIN = 5
    ELECTION_TIMEOUT_MAX = 10
    RPC_TIMEOUT          = 0.5

    # Raft Node types
    class Type(Enum):
        LEADER    = 1
        CANDIDATE = 2
        FOLLOWER  = 3

    def __init__(self, application : Any, addr: Address, contact_addr: Address = None):
        # Randomze timeout
        random_float = random.uniform(RaftNode.ELECTION_TIMEOUT_MIN, RaftNode.ELECTION_TIMEOUT_MAX)
        socket.setdefaulttimeout(RaftNode.RPC_TIMEOUT)

        # Raft Node attributes
        self.leader_id:                 int = -1
        self.address:                   Address = addr
        self.type:                      RaftNode.Type = RaftNode.Type.FOLLOWER
        self.log:                       List[int, str, str, int] = []
        self.app:                       KVStore =  application

        # Raft Node election state
        self.election_term:             int = 0
        self.election_timeout:          int = time.time() + random_float
        self.election_interval:         int = random_float
        self.voted_for:                 int = -1
        self.vote_count:                int = 0

        # Raft Node log state
        self.commit_index:              int = -1
        self.last_applied:              int = -1
        self.last_heartbeat_received:   int = time.time()

        # Raft Node cluster state
        self.match_index:               Dict[str, int] = {}
        self.next_index:                Dict[str, int] = {}

        # Raft Node cluster membership
        self.cluster_addr_list:         List[Address] = []
        self.cluster_leader_addr:       Address = None


        # Leader node
        if contact_addr is None:
            self.cluster_addr_list.append(self.address)
            self.__initialize_as_leader()
        # Follower node
        else:
            self.__initialize_as_follower()
            self.election_term = 0
            self.__try_to_apply_membership(contact_addr)


    # Logging
    def __print_log(self, text: str):
        print(f"[{self.address}] [{time.strftime('%H:%M:%S')}] {text}")


    # Leader initialization
    def __initialize_as_leader(self):
        self.__print_log("Initialize as leader node...")
        self.cluster_leader_addr = self.address
        self.type = RaftNode.Type.LEADER
        request = {
            "cluster_leader_addr": self.address
        }

        # Heartbeat interval
        self.heartbeat_thread = Thread(target=asyncio.run,args=[self.__leader_heartbeat()])
        self.heartbeat_thread.start()


    # Follower initialization
    def __initialize_as_follower(self):
        self.__print_log("Initialize as follower node...")
        self.type = RaftNode.Type.FOLLOWER

        # Election timeout
        self.timeout_thread = Thread(target=asyncio.run,args=[self.__election_timeout()])
        self.timeout_thread.start()


    # Leader heartbeat
    async def __leader_heartbeat(self):
        while True:
            self.__print_log("[Leader] Sending heartbeat...")
            for addr in self.cluster_addr_list:
                if Address(addr['ip'], addr['port']) == self.address:
                    continue
                # Send entries to follower
                self.append_entries(addr)

            await asyncio.sleep(RaftNode.HEARTBEAT_INTERVAL)


    # Election timeout
    async def __election_timeout(self):
        while True:
            if time.time() > self.election_timeout and self.type == RaftNode.Type.FOLLOWER:
                self.__print_log("Election timeout")
                self._reset_election_timeout()
                self.type = RaftNode.Type.CANDIDATE
                await self.__start_election()
                self.__initialize_as_follower()
                break

            await asyncio.sleep(self.election_interval)


    # Append entries
    def append_entries(self, follower_addr: Address) -> "json":
        # Initialization
        self.last_heartbeat_received = time.time()
        print(self.cluster_addr_list)
        self._reset_election_timeout()
        prev_log_index = len(self.log) - 1
        prev_log_term = 0
        if self.log:
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

        index = self.next_index.get(str(follower_addr), 0)

        # Check if there are entries to send
        if prev_log_index >= index:
            request["entries"] = self.log[index + 1:]
            self.__print_log(f"Sending append_entries to {follower_addr} with entries {request['entries']}")
            self.__print_log(self.log)
            # Send request to the follower
            response = self.__send_request(request, "append_entry", follower_addr)

            self.next_index.setdefault(str(follower_addr), -1)
            self.match_index.setdefault(str(follower_addr), -1)

            # Failed to append entries
            if not response["success"]:
                if self.next_index[str(follower_addr)] > 0:
                    self.next_index[str(follower_addr)] -= 1
            # Successfully appended entries
            else:
                self.match_index[str(follower_addr)] = prev_log_index
                self.next_index[str(follower_addr)] = prev_log_index
        else:
            response = self.__send_request(request, "append_entry", follower_addr)

        return response


    # Reset election timeout
    def _reset_election_timeout(self):
        random_float =  random.uniform( RaftNode.ELECTION_TIMEOUT_MIN, RaftNode.ELECTION_TIMEOUT_MAX)
        self.election_timeout = time.time() + random_float
        self.election_interval = random_float


    # Start election
    async def __start_election(self):
        self._reset_election_timeout()
        self.election_term += 1
        self.vote_count = 1
        self.voted_for = self.address

        self.__print_log(f"Starting election for term {self.election_term}")
        await self.__request_votes()


    # Request votes from other nodes
    async def __request_votes(self):
        request = {
            "term": self.election_term,
            "candidate_address": self.address,
            "last_log_index": len(self.log) - 1,
        }
        vote_request_tasks = []

        # Determine majority threshold
        if len(self.cluster_addr_list) <= 2:
            majority_threshold = 1
        else:
            majority_threshold = len(self.cluster_addr_list) // 2 + 1

        # Request votes from other nodes
        for addr in self.cluster_addr_list:
            addr = Address(addr['ip'], addr['port'])
            if addr == self.address or addr == self.cluster_leader_addr:
                continue
            self.__print_log(f"Requesting vote from {addr.ip}:{addr.port}")
            try:
                # Send asynchronous vote request
                task = self.__send_request_async(request, "request_vote", addr)
                vote_request_tasks.append(task)
            except TimeoutError:
                self.__print_log(f"Vote request to {addr.ip}:{addr.port} timed out")
                continue
            except Exception as e:
                self.__print_log(f"Error requesting vote from {addr.ip}:{addr.port}: {str(e)}")
                continue

        if len(vote_request_tasks) == 0:
            self.__print_log("No other nodes to request votes from")
        else:
            # After all vote requests are sent
            for task in asyncio.as_completed(vote_request_tasks):
                try:
                    response = await task
                    if "vote_granted" in response and response["vote_granted"]:
                        self.vote_count += 1
                        self._reset_election_timeout()
                        self.__print_log("+1 Vote granted")
                except Exception as e:
                    self.__print_log(f"Error processing vote response: {str(e)}")
                    continue

        # Check if majority votes are received
        if self.vote_count >= majority_threshold:
            self.__print_log("Received majority votes, elected as leader")
            self.type = RaftNode.Type.LEADER
            self.__initialize_as_leader()


    # Apply for membership
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
            # Send request to the contact address
            response        = self.__send_request(self.address, "apply_membership", redirected_addr)
        self.log                 = response["log"]
        for addr in response["cluster_addr_list"]:
            self.cluster_addr_list.append(Address(addr["ip"], addr["port"]))
        self.cluster_leader_addr = redirected_addr


    # Send request
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
    

    # Send request async
    async def __send_request_async(self, request: Any, rpc_name: str, addr: Address) -> "json":
        if not isinstance(addr, Address):
            addr = Address(addr["ip"], addr["port"])

        node = aioxmlrpc.client.ServerProxy(f"http://{addr.ip}:{addr.port}")
        json_request = json.dumps(request)
        rpc_function = getattr(node, rpc_name)
        response = {
            "success": False,
        }
        
        try:
            response = await rpc_function(json_request)
            response = json.loads(response)
            self.__print_log(response)
        except KeyboardInterrupt:
            exit(1)
        except:
            self.__print_log(f"[{addr}] Is not replying (nack)")

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