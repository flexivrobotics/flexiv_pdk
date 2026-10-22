"""
Example: Create a system setup in the PDK server by connecting to an RDK and saving its configuration to the PDK server.

This script demonstrates how to:
  1. Remove existing workcell and create a new one
  2. Add a robot system to the scene by connecting to an RDK and saving its configuration to the PDK server
  3. List existing systems in the scene

Note: Remember to modify the `serial_number` variable to match your RDK's serial number before running the script.
"""
import os
import grpc

from flexiv.pdk import Client

from flexiv.pdk.workcell.workcell_service_pb2 import CreateRequest, NameRequest
from flexiv.pdk.config_service_pb2 import ListConfigRequest, ConfigType
from flexiv.pdk.system.system_service_pb2 import AddConnectedSystemRequest

def main():
    target = os.environ.get("PDK_SERVER_ADDR", "localhost:50052")
    print(f"Connecting to the PDK server at {target}...")

    # We use insecure channel, wrapped in our Client
    with Client(target) as client:
        workcell_name = "example_workcell"

        # 1. Remove any existing workcell
        print(f"Removing any existing workcell with name: {workcell_name}")
        try:
            client.workcell.stub.Remove(NameRequest(name=workcell_name))
        except grpc.RpcError as e:
            print(f"Remove workcell failed or not present: {e}")

        # 2. Create a workcell        
        print(f"Creating workcell: {workcell_name}")
        req = CreateRequest(name=workcell_name, description="A dual-robot setup with objects")
        try:
            client.workcell.stub.Create(req)
            client.workcell.stub.Load(NameRequest(name=workcell_name))
        except grpc.RpcError as e:
            print(f"Workcell operation failed or environment not running a server yet: {e}")

        # 3. Add a robot system to the scene
        print("Add a system by connecting to the RDK and saving its configuration to the PDK server")
        system_name = "system_1"
        serial_number = "Rizon4-062065"
        try:
            # Load the system from RDK
            add_system_response = client.system.stub.AddConnectedSystem(AddConnectedSystemRequest(name=system_name, serial_number=serial_number))

            if add_system_response.status.code == 0:
                print(f"Successfully added system: {system_name} with serial number: {serial_number}")
            else:
                print(f"Failed to add system: {system_name} with serial number: {serial_number}")

        except grpc.RpcError as e:
            print(f"System operation failed: {e}")

        # 4. List existing systems in the scene
        try:
            list_systems_response = client.config.stub.List(ListConfigRequest(type=ConfigType.CONFIG_TYPE_SYSTEM))
            print("Existing systems in the scene:")
            for sys in list_systems_response.names:
                print(f"- {sys}")
        except grpc.RpcError as e:
            print(f"Failed to list systems: {e}")


if __name__ == "__main__":
    main()