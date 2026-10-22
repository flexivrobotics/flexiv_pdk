"""
Example: Create a workcell, add a robot system, and query the components service using the Flexiv PDK.

This script demonstrates how to:
  1. Create a new workcell
  2. Add one robot system to the scene
  3. Query the components service for information about the robot system and available components
  4. Create a custom tool using the components service
"""
import os
import grpc
from google.protobuf import empty_pb2

from flexiv.pdk import Client
from flexiv.pdk.workcell.workcell_service_pb2 import CreateRequest, NameRequest
from flexiv.pdk.system.system_service_pb2 import GetUrdfRequest, GetArmSerialNumberRequest
from flexiv.pdk.config_service_pb2 import SaveConfigRequest
from flexiv.pdk.scene.object_pb2 import Object
from flexiv.pdk.system.system_pb2 import System
from flexiv.pdk.system.components.manipulator_pb2 import Manipulator
from flexiv.pdk.system.components.tool_pb2 import Tool
from flexiv.pdk.config_header_pb2 import ConfigHeader
from flexiv.pdk.spatial.geometry_pb2 import SE3Pose, Vector3, Quaternion
from flexiv.pdk.spatial.shape_pb2 import Collision, Visual, Shape, Box
from flexiv.pdk.system.components.custom_tool_pb2 import CustomTool
from flexiv.pdk.system.components.custom_tool_adapter_pb2 import CustomToolAdapter
from flexiv.pdk.system.components_service_pb2 import SaveCustomToolRequest, SaveCustomToolAdapterRequest


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


        # 3. Create a custom tool
        print("")
        print("Creating custom tool...")
        dummy_shape = Shape(box=Box(size=[0.05, 0.05, 0.05]))
        dummy_origin = SE3Pose(
            position=Vector3(x=0.0, y=0.0, z=0.05),
            rotation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)
        )
        custom_tool = CustomTool(
            manufacturer="example_manufacturer",
            model="example_model",
            tcp=SE3Pose(
                position=Vector3(x=0.0, y=0.0, z=0.1),
                rotation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)
            ),
            collision=[Collision(origin=dummy_origin, shape=dummy_shape)],
            visual=[Visual(origin=dummy_origin, shape=dummy_shape)]
        )
        try:
            save_tool_response = client.system_config.stub.SaveCustomTool(
                SaveCustomToolRequest(custom_tool=custom_tool)
            )
            if save_tool_response.status.code == 0:
                print("Custom tool saved successfully.")
            else:
                print(f"SaveCustomTool returned status: {save_tool_response.status}")
        except grpc.RpcError as e:
            print(f"SaveCustomTool failed: {e}")

        # 4. Create a custom tool adapter
        print("")
        print("Creating custom tool adapter...")
        custom_tool_adapter = CustomToolAdapter(
            manufacturer="example_manufacturer",
            model="example_model",
            flange=[SE3Pose(
                position=Vector3(x=0.0, y=0.0, z=0.0),
                rotation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)
            )]
        )
        try:
            save_tool_adapter_response = client.system_config.stub.SaveCustomToolAdapter(
                SaveCustomToolAdapterRequest(custom_tool_adapter=custom_tool_adapter)
            )
            if save_tool_adapter_response.status.code == 0:
                print("Custom tool adapter saved successfully.")
            else:
                print(f"SaveCustomToolAdapter returned status: {save_tool_adapter_response.status}")
        except grpc.RpcError as e:
            print(f"SaveCustomToolAdapter failed: {e}")

        # 5. List the available tool adapters
        print("")
        print("Listing tool adapters...")
        try:
            tool_adapters_response = client.system_config.stub.ListToolAdapters(empty_pb2.Empty())
            if (tool_adapters_response.status.code == 0):
                for item in tool_adapters_response.items:
                    print(f"Tool adapter manufacturer: {item.manufacturer}, model: {item.model}")   

        except grpc.RpcError as e:
            print(f"ListToolAdapters failed: {e}")

        # 6. List the available tools
        print("")
        print("Listing tools...")
        try:
            tools_response = client.system_config.stub.ListTools(empty_pb2.Empty())
            if (tools_response.status.code == 0):
                for item in tools_response.items:
                    print(f"Tool manufacturer: {item.manufacturer}, model: {item.model}")
        except grpc.RpcError as e:
            print(f"ListTools failed: {e}")

        # 7. List the available custom tools
        print("")
        print("Listing custom tools...")
        try:
            custom_tools_response = client.system_config.stub.ListCustomTools(empty_pb2.Empty())
            if (custom_tools_response.status.code == 0):
                for item in custom_tools_response.items:
                    print(f"Custom tool manufacturer: {item.manufacturer}, model: {item.model}")
        except grpc.RpcError as e:
            print(f"ListCustomTools failed: {e}")

        # 8. List the available custom tool adapters
        print("")
        print("Listing custom tool adapters...")
        try:
            custom_tool_adapters_response = client.system_config.stub.ListCustomToolAdapters(empty_pb2.Empty())
            if (custom_tool_adapters_response.status.code == 0):
                for item in custom_tool_adapters_response.items:
                    print(f"Custom tool adapter manufacturer: {item.manufacturer}, model: {item.model}")
        except grpc.RpcError as e:
            print(f"ListCustomToolAdapters failed: {e}")

        # 9. List the available external robot axes
        print("")
        print("Listing external robot axes...")
        try:
            axes_response = client.system_config.stub.ListExternalRobotAxes(empty_pb2.Empty())
            if (axes_response.status.code == 0):
                for item in axes_response.items:
                    print(f"External robot axis manufacturer: {item.manufacturer}, model: {item.model}")
        except grpc.RpcError as e:
            print(f"ListExternalRobotAxes failed: {e}")

        # 10. Add a robot system to the scene with the custom tool from step 3
        # Helper to construct header
        def make_header(name, parent="world", px=0.0, py=0.0, pz=0.0, rw=1.0, rx=0.0, ry=0.0, rz=0.0):
            return ConfigHeader(
                name=name,
                parent=parent,
                pose_in_parent=SE3Pose(
                    position=Vector3(x=px, y=py, z=pz),
                    rotation=Quaternion(x=rx, y=ry, z=rz, w=rw)
                )
            )

        print("")
        print("Saving robot system with custom tool to the scene...")
        sys2 = System(
            header=make_header("system_2", px=1.0, py=0.0, pz=0.0),
            control_box_serial_number="CX01-01-T1-000002",
            manipulator=Manipulator(
                name="arm",
                arm_serial_number="A02L-00-M3-000002"
            ),
            tool=[Tool(
                name="example_tool",
                manufacturer="example_manufacturer",
                model="example_model"
            )]
        )
        try:
            client.config.stub.Save(SaveConfigRequest(system=sys2))
        except grpc.RpcError:
            pass

        # 11. Get the system urdf
        print("Getting system urdf...")
        try:
            urdf_response = client.system.stub.GetUrdf(GetUrdfRequest(name="system_2"))
            if (urdf_response.status.code == 0):
                print(f"URDF for system_2:\n{urdf_response.urdf_content}")
        except grpc.RpcError as e:
            print(f"GetURDF failed: {e}")

        # 12. Get the arm serial number
        print("")
        print("Getting arm serial number...")
        try:
            arm_serial_response = client.system.stub.GetArmSerialNumber(GetArmSerialNumberRequest(system_name="system_2"))
            if (arm_serial_response.status.code == 0):
                print(f"Arm serial number for system_2: {arm_serial_response.arm_serial_number}")
                print(f"Arm public serial number for system_2: {arm_serial_response.arm_public_serial_number}")
        except grpc.RpcError as e:
            print(f"GetArmSerialNumber failed: {e}")


if __name__ == "__main__":
    main()