"""
Example: Filter a mesh object.

This script demonstrates how to:
  1. Create a new workcell
  2. Add a plane mesh object to the scene
  3. Filter a mesh using the mesh operation service

  Note: To run this example, copy the plane mesh file "plane_1m_10x10.obj" in the assets directory to "flexiv_pdk_data/user_data/meshes/" on the server machine. That folder is beside your flexiv_pdk folder.
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
from flexiv.pdk.spatial.shape_pb2 import Visual, Mesh, Shape, Collision

from flexiv.pdk.mesh_operation.service_pb2 import  FilterMeshRequest
from flexiv.pdk.mesh_operation.filter.parameters_pb2 import SmoothMesh

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

def make_mesh_visual(origin, mesh_path, scale=1.0):
    return Visual(
        origin=SE3Pose(
            position=Vector3(x=origin[0], y=origin[1], z=origin[2]),
            rotation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)
        ),
        shape=Shape(
            mesh=Mesh(
                filename=mesh_path,
                scale=Vector3(x=scale, y=scale, z=scale)
            )
        )
    )

def make_mesh_collision(origin, mesh_path, scale=1.0):
    return Collision(
        origin=SE3Pose(
            position=Vector3(x=origin[0], y=origin[1], z=origin[2]),
            rotation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)
        ),
        shape=Shape(
            mesh=Mesh(
                filename=mesh_path,
                scale=Vector3(x=scale, y=scale, z=scale)
            )
        )
    )

def main():
    target = os.environ.get("PDK_SERVER_ADDR", "localhost:50052")
    print(f"Connecting to the PDK server at {target}...")

    # We use insecure channel, wrapped in our Client
    with Client(target) as client:
        # 1. Create a workcell
        workcell_name = "example_workcell"

        # Remove any existing workcell
        print(f"Removing any existing workcell with name: {workcell_name}")
        try:
            client.workcell.stub.Remove(NameRequest(name=workcell_name))
        except grpc.RpcError as e:
            print(f"Remove workcell failed or not present: {e}")

        print(f"Creating workcell: {workcell_name}")
        req = CreateRequest(name=workcell_name, description="Example workcell for mesh filtering")
        try:
            client.workcell.stub.Create(req)
            client.workcell.stub.Load(NameRequest(name=workcell_name))
        except grpc.RpcError as e:
            print(f"Workcell operation failed or environment not running a server yet: {e}")        

        # 2. Add objects to the scene
        print("Saving objects to the scene...")        
        obj1 = Object(header=make_header("mesh_1", px=0.0, py=0.0, pz=0.0), 
                      visual=[make_mesh_visual((0.0, 0.0, 0.0), "/home/flexiv/user_data/meshes/plane_1m_10x10.obj")],
                      collision=[make_mesh_collision((0.0, 0.0, 0.0), "/home/flexiv/user_data/meshes/plane_1m_10x10.obj")])
        try:
            client.config.stub.Save(SaveConfigRequest(object=obj1))
        except grpc.RpcError:
            pass
        
        # 3. Filter mesh_1 using the MeshOperation service, and save the resulting mesh as a new object in the scene
        print("Filtering mesh and saving as new object...")
        filter_mesh_request = FilterMeshRequest(
            object_name="mesh_1",
            filtered_object_name_prefix="filtered_mesh_1",
            smooth_mesh=SmoothMesh(
                num_iterations=5,
                pass_band=0.1
            )
        )
        try:
            filter_mesh_response = client.mesh_operation.stub.FilterMesh(filter_mesh_request)
            if filter_mesh_response.status.code == 0:
                print(f"Mesh filtering successful, filtered objects saved as: {list(filter_mesh_response.filtered_object_names)}")
            else:
                print(f"Mesh filtering failed: {filter_mesh_response.status.message}")
                return
        except grpc.RpcError as e:
            print(f"Mesh filtering failed: {e}")



if __name__ == "__main__":
    main()