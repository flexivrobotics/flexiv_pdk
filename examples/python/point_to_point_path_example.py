"""
Example: Create a simple scene and run point-to-point path planning queries using the Flexiv PDK.

This script demonstrates how to:
  1. Create a new workcell
  2. Add multiple objects to the scene
  3. Add one robot system to the scene
  4. Create collision configurations
  5. Run point-to-point path planning queries with different collision configurations
"""
import os
import grpc
import time
import numpy as np

from flexiv.pdk import Client
from flexiv.pdk.workcell.workcell_service_pb2 import CreateRequest, NameRequest
from flexiv.pdk.config_service_pb2 import SaveConfigRequest, TypeNameConfigRequest, CONFIG_TYPE_P2P_PATH
from flexiv.pdk.system.system_pb2 import System
from flexiv.pdk.scene.object_pb2 import Object
from flexiv.pdk.scene.collision.collision_config_pb2 import CollisionConfig, CollisionPair
from flexiv.pdk.scene.collision.collision_service_pb2 import SaveRequest as CollisionSaveRequest
from flexiv.pdk.point_to_point_path.service_pb2 import PointToPointPathRequest, PTPJointWaypoints
from flexiv.pdk.config_header_pb2 import ConfigHeader
from flexiv.pdk.spatial.geometry_pb2 import SE3Pose, Vector3, Quaternion


def make_header(name, parent="world", px=0.0, py=0.0, pz=0.0, rw=1.0, rx=0.0, ry=0.0, rz=0.0):
    return ConfigHeader(
        name=name,
        parent=parent,
        pose_in_parent=SE3Pose(
            position=Vector3(x=px, y=py, z=pz),
            rotation=Quaternion(x=rx, y=ry, z=rz, w=rw)
        )
    )

def make_box(name, parent="world", px=0.0, py=0.0, pz=0.0, size_x=0.1, size_y=0.1, size_z=0.1):
    obj = Object(header=make_header(name, parent=parent, px=px, py=py, pz=pz))

    visual = obj.visual.add()
    visual.origin.position.x = 0.0
    visual.origin.position.y = 0.0
    visual.origin.position.z = 0.0
    visual.origin.rotation.x = 0.0
    visual.origin.rotation.y = 0.0
    visual.origin.rotation.z = 0.0
    visual.origin.rotation.w = 1.0
    visual.shape.box.size.extend([size_x, size_y, size_z])

    collision = obj.collision.add()
    collision.origin.position.x = 0.0
    collision.origin.position.y = 0.0
    collision.origin.position.z = 0.0
    collision.origin.rotation.x = 0.0
    collision.origin.rotation.y = 0.0
    collision.origin.rotation.z = 0.0
    collision.origin.rotation.w = 1.0

    collision.shape.box.size.extend([size_x, size_y, size_z])
    return obj

def create_system(name, arm_serial_number, control_box_serial_number, px, py, pz):
    system = System(
        header=make_header(name, px=px, py=py, pz=pz),
        control_box_serial_number=control_box_serial_number,
    )

    system.manipulator_adapter.name = "manipulator_adapter"
    system.manipulator_adapter.mass = 0.0
    system.manipulator_adapter.inertia.extend([0.0] * 9)
    system.manipulator_adapter.xyz.extend([0.0, 0.0, 0.0])
    system.manipulator_adapter.rpy.extend([0.0, 0.0, 0.0])

    system.manipulator.name = "arm"
    system.manipulator.arm_serial_number = arm_serial_number
    system.manipulator.lower_limit.extend([-2.76] * 7)
    system.manipulator.upper_limit.extend([2.76] * 7)
    system.manipulator.home_position.extend([0.0] * 7)

    return system

def main():
    target = os.environ.get("PDK_SERVER_ADDR", "localhost:50052")
    workcell_name = "example_workcell"
    print(f"Connecting to the PDK server at {target}...")

    with Client(target) as client:
        # 1. Remove any existing workcell
        print(f"Removing any existing workcell with name: {workcell_name}")
        try:
            client.workcell.stub.Remove(NameRequest(name=workcell_name))
        except grpc.RpcError as e:
            print(f"Remove workcell failed or not present: {e}")

        # 2. Create and load workcell
        print(f"Creating workcell: {workcell_name}")
        try:
            client.workcell.stub.Create(CreateRequest(name=workcell_name, description="A dual-robot setup with objects"))
            client.workcell.stub.Load(NameRequest(name=workcell_name))
        except grpc.RpcError as e:
            print(f"Workcell operation failed: {e}")

        # 3. Add one robot system to the scene
        print("Saving robot system to the scene...")

        sys1 = create_system(
            "system_1", "A02L-00-M3-000001", "CX01-01-T1-000001", 0.0, 0.0, 0.0
        )
        try:
            client.config.stub.Save(SaveConfigRequest(system=sys1))
        except grpc.RpcError as e:
            print(f"Save system failed: {e}")

        print("Commands executed to create workcell, 3 objects, and 1 system in the scene!")

        # 4. Add objects to the environment, with one object attached to the system's flange
        print("Saving objects to the scene...")

        for obj in [
            make_box("box_1", "world", 0.5, 0.0, 0.0, 0.2, 0.2, 0.2),
            make_box("box_2", "world", 0.5, 0.5, 0.0, 0.2, 0.2, 0.2),
            make_box("box_3", "world", 0.5, 1.0, 0.0, 0.2, 0.2, 0.2),
            make_box("box_4", "system_1.arm.flange", 0.0, 0.0, 0.0251, 0.05, 0.05, 0.05),
        ]:
            try:
                client.config.stub.Save(SaveConfigRequest(object=obj))
            except grpc.RpcError as e:
                print(f"Save object failed: {e}")

        # 5. Collision configuration
        print("Creating collision configurations...")
        def save_collision_config(name, pairs, collision_margin):
            config = CollisionConfig(name=name, collision_margin=collision_margin)
            for n1, n2 in pairs:
                pair = CollisionPair(name1=n1, name2=n2)
                config.pairs.append(pair)
            try:
                client.collision.stub.Save(CollisionSaveRequest(collision_config=config))
            except grpc.RpcError as e:
                print(f"Save collision config failed: {e}")

        # Default collision configuration - no pairs are excluded
        save_collision_config("default_collision_config", [
        ], 0.0)

        # Collision configuration that excludes collisions between system_1.arm and box_1
        save_collision_config("collision_config_without_box_1", [
            ("system_1.arm", "box_1"),
        ], 0.0)

        # Collision configuration that excludes collisions between system_1.arm and box_1 and box 4 and box 1
        save_collision_config("collision_config_without_box_1_and_box_4", [
            ("system_1.arm", "box_1"),
            ("box_4", "box_1"),
        ], 0.0)

        # 6. Point-to-point path planning queries
        print("Running point-to-point path planning queries...")
        def run_plan(path_name, system_name, tcp_name, collision_config_name, joint_waypoints):
            req = PointToPointPathRequest(
                path_name=path_name,
                collision_config_name=collision_config_name,
                joint_waypoints=PTPJointWaypoints(
                    system_name=system_name,
                    tcp_name=tcp_name,
                    joint_waypoints=joint_waypoints,
                ),
            )
            try:
                resp = client.point_to_point_path.stub.Plan(req)
                print("")
                if (resp.status.code == 0):
                    print(f"Plan successful")

                    get_resp = client.config.stub.Get(
                        TypeNameConfigRequest(name=path_name, type=CONFIG_TYPE_P2P_PATH)
                    )
                    if get_resp.status.code == 0 and get_resp.HasField("p2p_path"):
                        path = get_resp.p2p_path
                        print(f"  Cartesian waypoints ({len(path.cartesian_waypoints)}):")
                        for i, wp in enumerate(path.cartesian_waypoints):
                            p = wp.pose.position
                            q = wp.pose.rotation
                            print(f"    [{i}] pos=({p.x:.4f}, {p.y:.4f}, {p.z:.4f})  "
                                  f"rot=({q.x:.4f}, {q.y:.4f}, {q.z:.4f}, {q.w:.4f})")
                        print(f"  Joint waypoints ({len(path.joint_waypoints)}):")
                        for i, wp in enumerate(path.joint_waypoints):
                            joints = ", ".join(f"{v:.4f}" for v in wp.position)
                            print(f"    [{i}] [{joints}]")
                    else:
                        print(f"  Failed to retrieve path: {get_resp.status.message}")


                else:
                    print(f"Plan failed with status code {resp.status.code}: {resp.status.message}")
            except grpc.RpcError as e:
                print(f"Plan failed: {e}")

        # Helper for joint waypoints
        from flexiv.pdk.spatial.waypoint_pb2 import JointWaypoint
        import math
        kDegToRad = math.pi / 180.0

        # 1. No collision
        run_plan(
            "ptp_path_1", "system_1", "system_1.arm.flange", "default_collision_config",
            [
                JointWaypoint(position=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
                JointWaypoint(position=[0.0, -40.0 * kDegToRad, 0.0, 90.0 * kDegToRad, 0.0, 40.0 * kDegToRad, 0.0])
            ]
        )
        # 2. With collision (between system_1.arm and box_1)
        run_plan(
            "ptp_path_2", "system_1", "system_1.arm.flange", "default_collision_config",
            [
                JointWaypoint(position=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
                JointWaypoint(position=[13.24 * kDegToRad, -69.97 * kDegToRad, 0.06 * kDegToRad, 112.91 * kDegToRad, 1.03 * kDegToRad, 92.89 * kDegToRad, 12.23 * kDegToRad])
            ]
        )
        # 3. With collision (between box_4 and box_1)
        run_plan(
            "ptp_path_3", "system_1", "system_1.arm.flange", "collision_config_without_box_1",
            [
                JointWaypoint(position=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
                JointWaypoint(position=[13.24 * kDegToRad, -69.97 * kDegToRad, 0.06 * kDegToRad, 112.91 * kDegToRad, 1.03 * kDegToRad, 92.89 * kDegToRad, 12.23 * kDegToRad])
            ]
        )

        # 4. No collision
        run_plan(
            "ptp_path_4", "system_1", "system_1.arm.flange", "collision_config_without_box_1_and_box_4",
            [
                JointWaypoint(position=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
                JointWaypoint(position=[13.24 * kDegToRad, -69.97 * kDegToRad, 0.06 * kDegToRad, 112.91 * kDegToRad, 1.03 * kDegToRad, 92.89 * kDegToRad, 12.23 * kDegToRad])
            ]
        )

        print("All scene setup and planning queries complete.")

if __name__ == "__main__":
    main()
