from lib.struct.address import Address
from lib.raft          import RaftNode
from lib.struct.KVStore           import KVStore

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

        def apply_membership(request):
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
