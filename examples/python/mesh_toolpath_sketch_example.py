"""
Example: Create a sketch toolpath from a plane mesh.

This script demonstrates how to:
  1. Create a new workcell
  2. Add a plane mesh object to the scene
  3. Generate a sketch path for a mesh using the surface finish service

  Note: To run this example, copy the plane mesh file "plane_1m_10x10.obj" in the assets directory to "flexiv_pdk_data/user_data/meshes/" on the server machine. That folder is beside your flexiv_pdk folder.
"""
import os
import grpc

from flexiv.pdk import Client
from flexiv.pdk.workcell.workcell_service_pb2 import CreateRequest, NameRequest
from flexiv.pdk.config_service_pb2 import SaveConfigRequest, TypeNameConfigRequest, CONFIG_TYPE_SURFACE_PATH
from flexiv.pdk.scene.object_pb2 import Object
from flexiv.pdk.system.system_pb2 import System
from flexiv.pdk.system.components.manipulator_pb2 import Manipulator
from flexiv.pdk.system.components.adapter_pb2 import Adapter
from flexiv.pdk.config_header_pb2 import ConfigHeader
from flexiv.pdk.spatial.geometry_pb2 import SE3Pose, Vector3, Quaternion
from flexiv.pdk.spatial.shape_pb2 import Visual, Mesh, Shape, Collision

from flexiv.pdk.surface_finish.service_pb2 import GenerateNominalPathRequest, CreateRobotMotionRequest, GetRequest, GenerateRCATrajectoryFileRequest
from flexiv.pdk.surface_finish.solver_preferences_pb2 import SolverPreferences
from flexiv.pdk.surface_finish.generator.mesh_sketch_path_pb2 import MeshSketchPath

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
        req = CreateRequest(name=workcell_name, description="Example workcell for mesh toolpath sketch generation")
        try:
            client.workcell.stub.Create(req)
            client.workcell.stub.Load(NameRequest(name=workcell_name))
        except grpc.RpcError as e:
            print(f"Workcell operation failed or environment not running a server yet: {e}")        

        # 2. Add plane mesh object to the scene
        print("Adding plane mesh object to the scene...")
        obj1 = Object(
            header=make_header("mesh_1", px=0.8, py=0.0, pz=0.0),
            visual=[make_mesh_visual((0.0, 0.0, 0.0), "/home/flexiv/user_data/meshes/plane_1m_10x10.obj")],
            collision=[make_mesh_collision((0.0, 0.0, 0.0), "/home/flexiv/user_data/meshes/plane_1m_10x10.obj")]
        )
        try:
            client.config.stub.Save(SaveConfigRequest(object=obj1))
        except grpc.RpcError:
            pass
             
        # 3. Run the surface finish service to generate a sketch path for the mesh. The specified points
        # are in the mesh's local frame, and the generated path will be saved as a new config in the scene.
        print("Generating sketch path for the mesh...")
        try:
            path_req = GenerateNominalPathRequest(
                header=ConfigHeader(
                    name="path_long_sketch",
                    parent="mesh_1"
                ),
                mesh_sketch_path=MeshSketchPath(
                    points=[
                        Vector3(x=-0.05, y=0.0, z=0.00),
                        Vector3(x=-0.45, y=0.0, z=0.00)],
                    blending_radius=0.0,
                    fixed_spacing=0.01,
                    align_with_initial_direction=True
                )
            )
            path_response = client.surface_finish.stub.GenerateNominalPath(path_req)
            if (path_response.status.code == 0) and len(path_response.path_names) > 0:
                print("Successfully generated sketch path for the mesh.")
            else:
                print(f"Surface finish service call failed: {path_response.status.message}")
                return
        except grpc.RpcError as e:
            print(f"Surface finish service call failed: {e}")
            return

        path_long_sketch_names = path_response.path_names            

if __name__ == "__main__":
    main()