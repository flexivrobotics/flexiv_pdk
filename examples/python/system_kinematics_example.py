"""
Example: Create a simple scene with a robot system and compute Forward Kinematics.
"""
import os
import time
import grpc

from flexiv.pdk import Client
from flexiv.pdk.workcell.workcell_service_pb2 import CreateRequest, NameRequest
from flexiv.pdk.config_service_pb2 import SaveConfigRequest
from flexiv.pdk.system.system_pb2 import System
from flexiv.pdk.system.components.manipulator_pb2 import Manipulator
from flexiv.pdk.config_header_pb2 import ConfigHeader
from flexiv.pdk.spatial.geometry_pb2 import SE3Pose, Vector3, Quaternion
from flexiv.pdk.system.kinematics_service_pb2 import FKRequest, IKRequest
from flexiv.pdk.scene.collision.collision_config_pb2 import CollisionConfig
from flexiv.pdk.scene.collision.collision_service_pb2 import SaveRequest as CollisionSaveRequest


def make_header(name, parent="world", px=0.0, py=0.0, pz=0.0, rw=1.0, rx=0.0, ry=0.0, rz=0.0):
    return ConfigHeader(
        name=name,
        parent=parent,
        pose_in_parent=SE3Pose(
            position=Vector3(x=px, y=py, z=pz),
            rotation=Quaternion(x=rx, y=ry, z=rz, w=rw)
        )
    )

def main():
    target = os.environ.get("PDK_SERVER_ADDR", "localhost:50052")
    print(f"Connecting to the PDK server at {target}...")

    with Client(target) as client:
        workcell_name = "example_workcell"
        print(f"Removing any existing workcell with name: {workcell_name}")
        try:
            client.workcell.stub.Remove(NameRequest(name=workcell_name))
        except grpc.RpcError as e:
            print(f"Remove workcell failed or not present: {e}")

        print(f"Creating workcell: {workcell_name}")
        req = CreateRequest(name=workcell_name, description="A single-robot setup for kinematics calculation")
        
        try:
            client.workcell.stub.Create(req)
            client.workcell.stub.Load(NameRequest(name=workcell_name))
        except grpc.RpcError as e:
            print(f"Workcell operation failed or environment not running a server yet: {e}")

        print("Saving robot system to the scene...")
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

        print("Saving collision configuration...")
        collision_config_name = "default_collision_config"
        try:
            client.collision.stub.Save(CollisionSaveRequest(
                collision_config=CollisionConfig(name=collision_config_name, collision_margin=0.0)
            ))
        except grpc.RpcError as e:
            print(f"Save collision config failed: {e}")

        print("Computing Forward Kinematics for system_1.arm.flange...")
        fk_pose = SE3Pose(
            position=Vector3(x=0.13599999999999995, y=-0.11000000000000004, z=1.2550000000000001),
            rotation=Quaternion(x=8.65956056235493e-17, y=0.70710678118654746, z=-1.7319121124709863e-16, w=0.70710678118654757)
        )
        try:
            fk_req = FKRequest(
                system_name="system_1", 
                target_frame_name="system_1.arm.flange", 
                joint_positions=[1.0, 0.4, 0.3, 1.5708, 0.5, 0.4, 0.0]
            )
            t0 = time.time()
            fk_res = client.kinematics.stub.ComputeFK(fk_req)
            elapsed_fk = (time.time() - t0) * 1000
            fk_pose = fk_res.pose
            print(f"\n--- Forward Kinematics Result ({elapsed_fk:.2f} ms) ---")
            print(fk_res)
            print("---------------------------------")
        except grpc.RpcError as e:
            print(f"Kinematics error: {e}")

        print("Computing Inverse Kinematics for system_1.arm.flange without seed...")
        try:
            target_pose = fk_pose
            ik_req = IKRequest(
                system_name="system_1", 
                target_frame_name="system_1.arm.flange", 
                target_pose=target_pose,
                collision_config_name=collision_config_name,
            )
            t0 = time.time()
            ik_res = client.kinematics.stub.ComputeIK(ik_req)
            elapsed_ik = (time.time() - t0) * 1000
            print(f"\n--- Inverse Kinematics Result ({elapsed_ik:.2f} ms) ---")
            print(ik_res)
            print("---------------------------------")
        except grpc.RpcError as e:
            print(f"Kinematics error: {e}")


        time.sleep(0.1)
        print("Computing Inverse Kinematics for system_1.arm.flange with seed...")
        try:
            target_pose = fk_pose
            ik_req = IKRequest(
                system_name="system_1", 
                target_frame_name="system_1.arm.flange", 
                target_pose=target_pose,
                joint_position_seed=[1.0, 0.4, 0.3, 1.5708, 0.5, 0.4, 0.0],
                collision_config_name=collision_config_name,
            )
            t0 = time.time()
            ik_res = client.kinematics.stub.ComputeIK(ik_req)
            elapsed_ik = (time.time() - t0) * 1000
            print(f"\n--- Inverse Kinematics Result ({elapsed_ik:.2f} ms) ---")
            print(ik_res)
            print("---------------------------------")
        except grpc.RpcError as e:
            print(f"Kinematics error: {e}")

if __name__ == "__main__":
    main()
