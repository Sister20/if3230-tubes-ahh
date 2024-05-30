from lib.struct.address import Address
from lib.raft          import RaftNode
from lib.struct.KVStore           import KVStore
from lib.struct.AppendEntry   import AppendEntry

from xmlrpc.server import SimpleXMLRPCServer
import sys
import json
import os
import signal


def start_serving(addr: Address, contact_node_addr: Address):
    print(f"Starting Raft Server at {addr.ip}:{addr.port}")
    with SimpleXMLRPCServer((addr.ip, addr.port)) as server:
        server.register_introspection_functions()
        server.register_instance(RaftNode(KVStore(), addr, contact_node_addr))

        def __success_append_entry_response():
            response = AppendEntry.Response(
                server.instance.election_term,
                True,
            )
            return json.dumps(response.to_dict())

        def __fail_append_entry_response():
            response = AppendEntry.Response(
                server.instance.election_term,
                False,
            )
            return json.dumps(response.to_dict())

        @server.register_function
        def apply_membership(request):
            print("Applying for membership... from ", request)
            request = json.loads(request)
            addr = Address(request["ip"], int(request["port"]))

            server.instance.cluster_addr_list.append(addr)

            server.instance.match_index[str(addr)] = -1
            server.instance.next_index[str(addr)] = -1

            return json.dumps(
                {
                    "status": "success",
                    "log": server.instance.log,
                    "cluster_addr_list": server.instance.cluster_addr_list,
                    "cluster_leader_addr": server.instance.cluster_leader_addr,
                }
            )

        @server.register_function
        def append_entry(request):
            """ 
            this function will get called via RPC call

            Should be the follower that receives this
            """
            # print("Received append_entry request from ", request)
            request = json.loads(request)
            addr = Address(request["leader_addr"]["ip"],
                           int(request["leader_addr"]["port"]))

            if request["term"] < server.instance.election_term:
                return __fail_append_entry_response()

            if server.instance.type == RaftNode.NodeType.CANDIDATE:
                server.instance.type = RaftNode.NodeType.FOLLOWER
    
            server.instance.cluster_leader_addr = addr
            server.instance._reset_election_timeout()
            server.instance.cluster_addr_list = request["cluster_addr_list"]

            # __heartbeat(request, addr)
            print("Current log: ", server.instance.log)
            if len(request["entries"]) != 0:
                __log_replication(request, addr)

            # if request["leader_commit_index"] > server.instance.commit_index:
            #     __commit_log(request, addr)

            return __success_append_entry_response()

        def __log_replication(request, addr):
            for entry in request["entries"]:
                server.instance.log.append(entry)

            return __success_append_entry_response()
        
        @server.register_function
        def request_vote(request):
            """
            this function will get called via RPC call

            Should be the candidate that receives this
            """
            request = json.loads(request)
            # print("Received request_vote request from ", request)
            addr = Address(request["candidate_address"]["ip"],
                           int(request["candidate_address"]["port"]))
            # if request["term"] < server.instance.election_term:
            #     return __fail_append_entry_response()

            # if server.instance.type == RaftNode.NodeType.LEADER:
            #     server.instance.type = RaftNode.NodeType.FOLLOWER

            server.instance.cluster_leader_addr = addr
            server.instance._reset_election_timeout()
            server.instance.election_term = request["term"]
            response = {
                "status": "success",
                "term": server.instance.election_term,
                "vote_granted": True
            }
            return json.dumps(response)

        @server.register_function
        def execute(request):
            request = json.loads(request)

            logs = [server.instance.election_term, request["command"], request["args"]]
            server.instance.log.append(logs)

            if request["command"] == "ping":
                response = {
                    "status": "success",
                    "ip": addr.ip,
                    "port": addr.port,
                    "message": "pong"
                }
                
                return json.dumps(response)   
            elif request["command"] == "set":
                server.instance.app.put(request["args"]["key"], request["args"]["value"])
                response = {
                    "status": "success",
                    "message": "Key-Value pair added successfully"
                }
                return json.dumps(response)      
            elif request["command"] == "get":
                value = server.instance.app.get(request["args"])
                response = {
                    "status": "success",
                    "value": value
                }
                return json.dumps(response)     
            elif request["command"] == "append":
                server.instance.app.append(request["args"]["key"], request["args"]["value"])
                response = {
                    "status": "success",
                    "message": "Value appended successfully"
                }
                return json.dumps(response)
            elif request["command"] == "delete":
                server.instance.app.delete(request["args"])
                response = {
                    "status": "success",
                    "message": "Key-Value pair deleted successfully"
                }
                return json.dumps(response)
            elif request["command"] == "strln":
                response = {
                    "status": "success",
                    "message": server.instance.app.strln(request["args"])
                }
                return json.dumps(response)
            elif request["command"] == "request_log":
                response = {
                    "status": "success",
                    "message": server.instance.log
                }
                return json.dumps(response)
            

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
            os.kill(os.getpid(), signal.SIGTERM)



if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: server.py ip port [contact_ip] [contact_port]")
        exit()

    contact_addr = None
    if len(sys.argv) == 5:
        contact_addr = Address(sys.argv[3], int(sys.argv[4]))
    server_addr = Address(sys.argv[1], int(sys.argv[2]))

    start_serving(server_addr, contact_addr)
