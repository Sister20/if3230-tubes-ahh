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

        command_input = input_validation(command)
        if command == -1:
            print("Invalid command")
            continue
        elif command_input == 0:
            break
        elif command_input == 1:
            request = {
                "command": "ping",
                "args": ""
            }
            response = __send_request(request, "execute", client_addr)

            if (response["status"] == "success"):
                if(response["message"]):
                    print(response["message"] + " from " + response["ip"] + ":" + str(response["port"]))
        elif command_input == 2:
            request = {
                "command": "set",
                "args" : {
                    "key": command[1],
                    "value": command[2]
                }
            }
            response = __send_request(request, "execute", client_addr)

            if (response["status"] == "success"):
                print("Key-Value pair added successfully")
            else:
                print("Failed to add Key-Value pair")

        elif command_input == 3:
            request = {
                "command": "get",
                "args": command[1]
            }
            response = __send_request(request, "execute", client_addr)

            if (response["status"] == "success"):
                print("Value: " + response["value"])
            else:
                print("Failed to get value")

        elif command_input == 4:
            request = {
                "command": "append",
                "args": {
                    "key": command[1],
                    "value": command[2]
                }
            }
            response = __send_request(request, "execute", client_addr)

            if (response["status"] == "success"):
                print(response["message"])
            else:
                print("Failed to append value")

        elif command_input == 5:
            request = {
                "command": "delete",
                "args": command[1]
            }
            response = __send_request(request, "execute", client_addr)

            if (response["status"] == "success"):
                print("Key-Value pair deleted successfully")
            else:
                print("Failed to delete Key-Value pair")

        elif command_input == 6:
            request = {
                "command": "strln",
                "args": command[1]
            }
            response = __send_request(request, "execute", client_addr)

            if (response["status"] == "success"):
                print("Length of the store: " + response["message"])
            else:
                print("Failed to get length of the store")


def input_validation(command):
    if command[0] =="exit":
        return 0
    if command[0] == "ping" and len(command) == 1:
        return 1
    if command[0] == "set" and len(command) == 3:
        return 2
    if command[0] == "get" and len(command) == 2:
        return 3
    if command[0] == "append" and len(command) == 3:
        return 4
    if command[0] == "delete" and len(command) == 2:
        return 5
    if command[0] == "strln" and len(command) == 2:
        return 6
    
    return -1
    

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