"""
Example: Create a toolpath sketch from a plane mesh and generate a RCA trajectory for a robot to follow the path.

This script demonstrates how to:
  1. Create a new workcell
  2. Add a plane mesh object to the scene
  3. Add a robot system to the scene
  4. Generate a sketch path for a mesh using the surface finish service
  5. Solve for the robot motion along the generated path
  6. Set Cartesian velocity, acceleration, and force for the robot motion
  7. Generate the RCA trajectory for the robot motion

  Note: To run this example, copy the plane mesh file "plane_1m_10x10.obj" in the assets directory to "flexiv_pdk_data/user_data/meshes/" on the server machine. That folder is beside your flexiv_pdk folder.
"""
import os
import grpc
import time

from flexiv.pdk import Client
from flexiv.pdk.workcell.workcell_service_pb2 import CreateRequest, NameRequest
from flexiv.pdk.config_service_pb2 import SaveConfigRequest, TypeNameConfigRequest, CONFIG_TYPE_SURFACE_PATH
from flexiv.pdk.scene.object_pb2 import Object
from flexiv.pdk.system.system_pb2 import System
from flexiv.pdk.system.components.manipulator_pb2 import Manipulator
from flexiv.pdk.config_header_pb2 import ConfigHeader
from flexiv.pdk.spatial.geometry_pb2 import SE3Pose, Vector3, Quaternion
from flexiv.pdk.spatial.shape_pb2 import Visual, Mesh, Shape

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
        req = CreateRequest(name=workcell_name, description="Example workcell for linear path trajectory generation")
        try:
            client.workcell.stub.Create(req)
            client.workcell.stub.Load(NameRequest(name=workcell_name))
        except grpc.RpcError as e:
            print(f"Workcell operation failed or environment not running a server yet: {e}")        

        # 2. Add plane mesh object to the scene
        print("Adding plane mesh object to the scene...")
        obj1 = Object(header=make_header("mesh_1", px=0.8, py=0.0, pz=0.0), visual=[make_mesh_visual((0.0, 0.0, 0.0), "/home/flexiv/user_data/meshes/plane_1m_10x10.obj")])
        try:
            client.config.stub.Save(SaveConfigRequest(object=obj1))
        except grpc.RpcError:
            pass
        
        # 3. Add a robot system to the scene
        print("Saving robot system to the scene...")
        sys1 = System(
            header=make_header("system_1", px=0.05, py=0.0, pz=0.0),
            control_box_serial_number="CX01-01-T1-000001",
            manipulator=Manipulator(
                name="arm",
                arm_serial_number="A02L-00-M3-000001"
            ),
        )
        try:
            client.config.stub.Save(SaveConfigRequest(system=sys1))
        except grpc.RpcError:
            pass

        # 4. Run the surface finish service to generate a sketch path for the mesh. The specified points
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
            if path_response.status.code != 0:
                print(f"Surface finish service call failed: {path_response.status.message}")
                return
            print("Successfully generated sketch path for the mesh.")
        except grpc.RpcError as e:
            print(f"Surface finish service call failed: {e}")
            return

        path_long_sketch_names = path_response.path_names

        
        # 5. Run Basic solve to compute the robot joint positions for the generated path
        print("Running basic solve for the generated long path...")
        try:
            for path_name in path_long_sketch_names:
                solve_req = CreateRobotMotionRequest(
                    path_name=path_name,
                    solver_preferences=SolverPreferences(
                        system_name="system_1",
                        tcp_ecp_name="system_1.arm.flange",
                        solver_type=SolverPreferences.SOLVER_TYPE_BASIC
                    )
                )
                solve_response = client.surface_finish.stub.CreateRobotMotion(solve_req)
                if (solve_response.status.code == 0):
                    print(f"Successfully created robot motion for path {path_name}.")
                else:
                    print(f"Failed to create robot motion for path {path_name}: {solve_response.status.message}")
        except grpc.RpcError as e:
            print(f"Failed to solve path config: {e}")
            return

        # 6. Get the generated path config and set the Cartesian 
        # velocity and acceleration for the robot motion
        print("Setting Cartesian velocity, acceleration, and force for the generated path...")
        try:
            for path_name in path_long_sketch_names:
                get_req = GetRequest(path_name=path_name)
                get_response = client.surface_finish.stub.Get(get_req)
                if (get_response.status.code == 0):
                    path_config = get_response.path
                    for waypoint in path_config.nominal_cartesian:
                        waypoint.velocity = 0.1
                        waypoint.acceleration = 0.2
                        waypoint.wrench.force.z = 5
                    for waypoint in path_config.refined_cartesian:
                        waypoint.velocity = 0.1
                        waypoint.acceleration = 0.2
                        waypoint.wrench.force.z = 5
                    save_req = SaveConfigRequest(surface_path=path_config)
                    client.config.stub.Save(save_req)
                    print(f"Successfully set Cartesian velocity, acceleration, and force for path {path_name}.")
                else:
                    print(f"Failed to get path config for {path_name}: {get_response.status.message}")
        except grpc.RpcError as e:
            print(f"Failed to get path config: {e}")
            return

        # 7. Generate the RCA trajectory for the robot motion. 
        # The generated trajectory .traj file will be saved in 
        # the PDK server as {workcell}/linear_path/{path_name}/{path_name}.traj.
        print("Generating RCA trajectory for the robot motion...")
        try:
            for path_name in path_long_sketch_names:
                generate_rca_traj_req = GenerateRCATrajectoryFileRequest(
                    path_name=path_name,
                )
                generate_rca_traj_response = client.surface_finish.stub.GenerateRCATrajectoryFile(generate_rca_traj_req)
                if (generate_rca_traj_response.status.code == 0):
                    print(f"Successfully created RCA trajectory for path {path_name}.")
                else:
                    print(f"Failed to create RCA trajectory for path {path_name}: {generate_rca_traj_response.status.message}")
        except grpc.RpcError as e:
            print(f"Failed to generate RCA trajectory: {e}")
            return

if __name__ == "__main__":
    main()