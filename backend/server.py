# Import structs
from lib.struct.address import Address
from lib.raft          import RaftNode
from lib.struct.KVStore           import KVStore

# Import libraries
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

        
        def check_membership(addr: Address) -> bool:
            for cluster_addr in server.instance.cluster_addr_list:
                print ("KONTOL",cluster_addr)
                if not isinstance(cluster_addr, Address):
                    cluster_addr = Address(addr["ip"], addr["port"])
                if cluster_addr.ip == addr.ip and cluster_addr.port == addr.port:
                    return True
            return False

        @server.register_function
        def apply_membership(request) -> str:
            print("Applying for membership... from ", request)
            request = json.loads(request)
            addr = Address(request["ip"], int(request["port"]))
            print(server.instance.cluster_addr_list)
            if (check_membership(addr) == False):
                server.instance.cluster_addr_list.append(addr)
            else:
                print("Already a member")

            print("SEND RESPONSE")
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
        def append_entry(request) -> str:
            print(server.instance.cluster_addr_list[0])
            request = json.loads(request)
            addr = Address(request["leader_addr"]["ip"],
                           int(request["leader_addr"]["port"]))

            if request["term"] < server.instance.election_term:
                response = {
                    "status": "late",
                    "term": server.instance.election_term
                }
                return json.dumps(response)
            if request["term"] >= server.instance.election_term:
                server.instance.election_term = request["term"]
                server.instance.type = RaftNode.Type.FOLLOWER
                server.instance.cluster_leader_addr = addr


            if server.instance.type == RaftNode.Type.CANDIDATE:
                server.instance.type = RaftNode.Type.FOLLOWER

            if server.instance.type == RaftNode.Type.LEADER:
                server.instance.cluster_leader_addr = addr
                server.instance.change_to_follower()
            
            server.instance.cluster_leader_addr = addr
            server.instance._reset_election_timeout()
            server.instance.cluster_addr_list = request["cluster_addr_list"]

            # __heartbeat(request, addr)
            print("Current log: ", server.instance.log)
            if len(request["entries"]) != len(server.instance.log):
                __log_replication(request, addr)

            if request["leader_commit"] > server.instance.commit_index:
                commit_logs = server.instance.log[server.instance.commit_index]
                commit_request = {
                    "command": commit_logs[1],
                    "args": commit_logs[2]
                }
                print("Committing log")
                commit_log(commit_request)
                server.instance.commit_index += 1

            response = {
                "status": "success",
                "term": server.instance.election_term,
            }
            return json.dumps(response)

        def __log_replication(request, addr):
            if len(server.instance.log) < len(request["entries"]):
                for i in range(len(server.instance.log), len(request["entries"])):
                    print("Replicating logs")
                    server.instance.log.append(request["entries"][i])

        
        @server.register_function
        def request_vote(request):
            request = json.loads(request)
            # print("Received request_vote request from ", request)
            addr = Address(request["candidate_address"]["ip"],
                           int(request["candidate_address"]["port"]))
            if request["term"] < server.instance.election_term:
                response = {
                    "status": "failed"
                }
                return json.dumps(response)

            if server.instance.type == RaftNode.Type.LEADER:
                server.instance.type = RaftNode.Type.FOLLOWER

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
        def execute(request) -> str:
            request = json.loads(request)
            if (server.instance.address.ip != server.instance.cluster_leader_addr.ip) or (server.instance.address.port != server.instance.cluster_leader_addr.port):
                print("Redirecting to leader")
                response = {
                    "status": "redirected",
                    "ip": server.instance.cluster_leader_addr.ip,
                    "port": server.instance.cluster_leader_addr.port
                }
                return json.dumps(response)
            logs = [server.instance.election_term, request["command"], request["args"]]
            server.instance.log.append(logs)
            agree = 1
            for addr in server.instance.cluster_addr_list:
                if not isinstance(addr, Address):
                    addr = Address(addr["ip"], addr["port"])
                if addr != server.instance.address:
                    try :
                        response = server.instance.append_entries(addr)
                        if response["success"]:
                            agree += 1
                    except:
                        pass
            if len(server.instance.cluster_addr_list) == 2:
                threshold = 1
            else:
                threshold = len(server.instance.cluster_addr_list) // 2 + 1
            if agree >= threshold:
                server.instance.commit_index += 1
                response = commit_log(request)
                return response
            
            else:
                response = {
                    "status": "failed",
                    "message": "Failed to commit log"
                }
                return json.dumps(response)

           
        def commit_log(request):
            print ("COMMIT", request)
            if request["command"] == "ping":
                response = {
                    "status": "success",
                    "ip": addr.ip,
                    "port": addr.port,
                    "message": "pong"
                }   
                return json.dumps(response)   
            elif request["command"] == "set":
                print("SET", request["args"]["key"], request["args"]["value"], "address", server.instance.address)
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
