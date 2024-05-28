from lib.struct.address import Address
from xmlrpc.client import ServerProxy
from typing        import Any, List, Dict
import json
import sys
import traceback


def start_client(client_addr: Address):
    print(f"Starting client at {client_addr.ip}:{client_addr.port}")

    while True:
        command = input("Enter command: ")
        command = command.split()

        if not input_validation(command):
            print("Invalid command")
            continue
        else:
            if command[0] == "exit":
                break
            elif command[0] == "ping":
                request = {
                    "command": "ping",
                    "args": ""
                }
                response = __send_request(request, "execute", client_addr)

                if (response["status"] == "success"):
                    if(response["message"]):
                        print(response["message"] + " from " + response["ip"] + ":" + str(response["port"]))


def input_validation(command):
    if command[0] =="exit":
        return True
    if command[0] == "ping" and len(command) == 1:
        return True
    

def __send_request(request: Any, rpc_name: str, addr: Address) -> "json":
    node = ServerProxy(f"http://{addr.ip}:{addr.port}")
    json_request = json.dumps(request)
    rpc_function = getattr(node, rpc_name)
    response = {
        "status": "failed",
        "ip": addr.ip,
        "port": addr.port
    }
    while response["status"] == "failed":
        print("[REQUEST] Sending to server")
        try:
            response = json.loads(rpc_function(json_request))
        except KeyboardInterrupt:
            break
        except:
            traceback.print_exc()
            print("[RESPONSE] Can't connect to server. retrying...")
            continue

    return response
        
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("client.py <ip> <port>")
        exit()

    client_addr = Address(sys.argv[1], int(sys.argv[2]))

    start_client(client_addr)