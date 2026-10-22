"""
Example: Create a simple scene using the Flexiv PDK.

This script demonstrates how to:
  1. Create a new workcell
  2. Add multiple objects to the scene
  3. Add two robot systems to the scene, separated by 1.4 meters and facing each other
"""
import os
import grpc

from flexiv.pdk import Client
from flexiv.pdk.workcell.workcell_service_pb2 import CreateRequest, NameRequest
from flexiv.pdk.config_service_pb2 import SaveConfigRequest
from flexiv.pdk.scene.object_pb2 import Object
from flexiv.pdk.system.system_pb2 import System
from flexiv.pdk.system.components.manipulator_pb2 import Manipulator
from flexiv.pdk.config_header_pb2 import ConfigHeader
from flexiv.pdk.spatial.geometry_pb2 import SE3Pose, Vector3, Quaternion


def main():
    target = os.environ.get("PDK_SERVER_ADDR", "localhost:50052")
    print(f"Connecting to the PDK server at {target}...")

    # We use insecure channel, wrapped in our Client
    with Client(target) as client:
        # 1. Create a workcell
        workcell_name = "example_workcell"
        print(f"Removing any existing workcell with name: {workcell_name}")
        try:
            client.workcell.stub.Remove(NameRequest(name=workcell_name))
        except grpc.RpcError as e:
            print(f"Remove workcell failed or not present: {e}")

        print(f"Creating workcell: {workcell_name}")
        req = CreateRequest(name=workcell_name, description="A dual-robot setup with objects")
        try:
            client.workcell.stub.Create(req)
            client.workcell.stub.Load(NameRequest(name=workcell_name))
        except grpc.RpcError as e:
            print(f"Workcell operation failed or environment not running a server yet: {e}")

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

        # 2. Add objects to the scene
        print("Saving objects to the scene...")

        # Required fields for Object: header
        # (header requires: name, parent, pose_in_parent)
        # Optional Object fields: inertial, collision, reference_only, visual
        
        # Object 1
        obj1 = Object(header=make_header("box_1", px=0.5, py=0.0, pz=0.0))
        try:
            client.config.stub.Save(SaveConfigRequest(object=obj1))
        except grpc.RpcError:
            pass
        
        # Object 2
        obj2 = Object(header=make_header("box_2", px=0.5, py=0.5, pz=0.0))
        try:
            client.config.stub.Save(SaveConfigRequest(object=obj2))
        except grpc.RpcError:
            pass

        # Object 3
        obj3 = Object(header=make_header("box_3", px=0.5, py=1.0, pz=0.0))
        try:
            client.config.stub.Save(SaveConfigRequest(object=obj3))
        except grpc.RpcError:
            pass

        # 3. Add two robot systems to the scene
        print("Saving robot systems to the scene...")

        # System 1: Placed at x=-0.7, facing +x (rz=0)
        sys1 = System(
            header=make_header("system_1", px=-0.7, py=0.0, pz=0.0),
            control_box_serial_number="CX01-01-T1-000001",
            manipulator=Manipulator(
                name="arm",
                arm_serial_number="A02L-00-M3-000001"
            )
        )
        try:
            client.config.stub.Save(SaveConfigRequest(system=sys1))
        except grpc.RpcError:
            pass

        # System 2: Placed at x=0.7, facing -x (rz=1, rw=0 -> 180 degrees around Z)
        sys2 = System(
            header=make_header("system_2", px=0.7, py=0.0, pz=0.0, rw=0.0, rz=1.0),
            control_box_serial_number="CX01-01-T1-000002",
            manipulator=Manipulator(
                name="arm",
                arm_serial_number="A02L-00-M3-000002"
            )
        )
        try:
            client.config.stub.Save(SaveConfigRequest(system=sys2))
        except grpc.RpcError:
            pass
        
        print("Commands executed to create workcell, 3 objects, and 2 systems in the scene!")


if __name__ == "__main__":
    main()