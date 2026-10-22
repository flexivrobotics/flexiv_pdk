"""
Example: Create system pose target waypoints from forward kinematics and use them to plan a point-to-point path.

This script demonstrates how to:
  1. Create a new workcell
  2. Add a robot system to the scene
  3. Compute forward kinematics for a joint configuration and save the result as a system pose
     target waypoint attached to the system
  4. Retrieve a saved system pose target waypoint from the scene
  5. Create a collision configuration, required by the point-to-point path service
  6. Run a point-to-point path plan referencing saved system pose target waypoints by name
"""
import os
import grpc

from flexiv.pdk import Client
from flexiv.pdk.workcell.workcell_service_pb2 import CreateRequest, NameRequest
from flexiv.pdk.config_service_pb2 import SaveConfigRequest, TypeNameConfigRequest, CONFIG_TYPE_SYSTEM_POSE
from flexiv.pdk.system.system_pb2 import System
from flexiv.pdk.system.components.manipulator_pb2 import Manipulator
from flexiv.pdk.config_header_pb2 import ConfigHeader
from flexiv.pdk.spatial.geometry_pb2 import SE3Pose, Vector3, Quaternion
from flexiv.pdk.scene.target_waypoint_pb2 import TargetWaypoint
from flexiv.pdk.spatial.waypoint_pb2 import CartesianWaypoint, JointWaypoint
from flexiv.pdk.scene.collision.collision_config_pb2 import CollisionConfig
from flexiv.pdk.scene.collision.collision_service_pb2 import SaveRequest as CollisionSaveRequest
from flexiv.pdk.point_to_point_path.service_pb2 import PointToPointPathRequest, PTPTargetWaypoints
from flexiv.pdk.system.kinematics_service_pb2 import FKRequest


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

        # 3. Add a robot system to the scene
        print("Saving robot system to the scene...")

        # System 1
        sys1 = System(
            header=make_header("system_1", px=-0.0, py=0.0, pz=0.0),
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

        # 4. Run a forward kinematics on the first joint configuration
        joint_configuration_1 = [1.0, 0.4, 0.3, 1.5708, 0.5, 0.4, 0.0]
        try:
            fk_req = FKRequest(
                system_name="system_1", 
                target_frame_name="system_1.arm.flange", 
                joint_positions=joint_configuration_1
            )
            fk_res = client.kinematics.stub.ComputeFK(fk_req)
            fk_pose_1 = fk_res.pose
            print("---------------------------------")
        except grpc.RpcError as e:
            print(f"Kinematics error: {e}")

        # 5. Add a system pose object to the scene, attached to system_1
        print("Saving system pose object to the scene...")
        system_pose_object = TargetWaypoint(
            header=make_header("system_pose_1", parent="system_1"),
            tcp_name="system_1.arm.flange",
            cartesian=CartesianWaypoint(
                pose=fk_pose_1,
            ),
            joint=JointWaypoint(
                position=joint_configuration_1
            )
        )

        try:
            client.config.stub.Save(SaveConfigRequest(system_pose=system_pose_object))
        except grpc.RpcError as e:
            print(f"Save system pose object failed: {e}")

        # 6. Get the system pose object back from the server to verify it was saved and can be retrieved
        print("Retrieving system pose object from the scene...")
        try:
            get_response = client.config.stub.Get(
                TypeNameConfigRequest(type=CONFIG_TYPE_SYSTEM_POSE, name="system_pose_1")
            )
            retrieved_system_pose = get_response.system_pose
            print(f"Retrieved system pose object: {retrieved_system_pose}")
        except grpc.RpcError as e:
            print(f"Get system pose object failed: {e}")

        # 7. Run a forward kinematics on the second joint configuration
        joint_configuration_2 = [1.0, 0.4, 0.3, 0, 0.5, 0.4, 0.0]
        try:
            fk_req = FKRequest(
                system_name="system_1", 
                target_frame_name="system_1.arm.flange", 
                joint_positions=joint_configuration_2
            )
            fk_res = client.kinematics.stub.ComputeFK(fk_req)
            fk_pose_2 = fk_res.pose
            print("---------------------------------")
        except grpc.RpcError as e:
            print(f"Kinematics error: {e}")

        # 8. Add a system pose object to the scene, attached to system_1
        print("Saving system pose object to the scene...")
        system_pose_object_2 = TargetWaypoint(
            header=make_header("system_pose_2", parent="system_1"),
            tcp_name="system_1.arm.flange",
            cartesian=CartesianWaypoint(
                pose=fk_pose_2,
            ),
            joint=JointWaypoint(
                position=joint_configuration_2
            )
        )

        try:
            client.config.stub.Save(SaveConfigRequest(system_pose=system_pose_object_2))
        except grpc.RpcError as e:
            print(f"Save system pose object failed: {e}")

        # 9. Create a default collision configuration, required by the point-to-point path service
        print("Creating default collision configuration...")
        try:
            client.collision.stub.Save(CollisionSaveRequest(
                collision_config=CollisionConfig(name="default_collision_config")
            ))
        except grpc.RpcError as e:
            print(f"Save collision config failed: {e}")

        # 10. Run a point-to-point path plan directly from the retrieved system pose target waypoints
        print("Running point-to-point path plan using the system pose target waypoints...")
        try:
            plan_response = client.point_to_point_path.stub.Plan(PointToPointPathRequest(
                path_name="ptp_path_system_pose_1",
                collision_config_name="default_collision_config",
                target_waypoints=PTPTargetWaypoints(
                    target_waypoint_names=["system_pose_1", "system_pose_2"]
                )
            ))
            if plan_response.status.code == 0:
                print("Point-to-point path plan successful")
            else:
                print(f"Point-to-point path plan failed: {plan_response.status.message}")
        except grpc.RpcError as e:
            print(f"Point-to-point path plan failed: {e}")


if __name__ == "__main__":
    main()