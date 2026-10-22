"""
Example: Run a reconstruction using the Flexiv PDK.

Note: To run this example, you need to have a Flexiv robot system with RDK remote mode enabled, and a camera with CAMID 9 enabled in the AIConsole in Noema Edge.
Modify the robot serial number and camera ID in the code below to match your setup. If the camera is a global camera, you should set the parent of the camera to "world" instead of "system_1.arm.flange".

This script demonstrates how to:
  1. Create a new workcell
  2. Add a robot system to the scene
  3. Add a camera to the scene
  4. Check whether the camera is online
  5. Add a reconstruction config
  6. Run a reconstruction using the camera and the config
  7. List available reconstruction objects
  8. Remove the camera from the reconstruction
  9. Remove the reconstruction config
"""
import os
import grpc
import time
from google.protobuf import empty_pb2

from flexiv.pdk import Client
from flexiv.pdk.workcell.workcell_service_pb2 import CreateRequest, NameRequest
from flexiv.pdk.camera.service_pb2 import CameraNameRequest

from flexiv.pdk.config_service_pb2 import SaveConfigRequest, TypeNameConfigRequest, ConfigType
from flexiv.pdk.scene.camera_pb2 import Camera
from flexiv.pdk.config_header_pb2 import ConfigHeader
from flexiv.pdk.spatial.geometry_pb2 import SE3Pose, Vector3, Quaternion
from flexiv.pdk.scene.reconstruction.service_pb2 import (
    StartReconstructionRequest,
    CameraNamesRequest,
    ReconstructionResultRequest,
)
from flexiv.pdk.scene.reconstruction.config_pb2 import ReconstructionConfig

from flexiv.pdk.system.system_service_pb2 import AddConnectedSystemRequest

def main():
    target = os.environ.get("PDK_SERVER_ADDR", "localhost:50052")
    print(f"Connecting to the PDK server at {target}...")

    # We use insecure channel, wrapped in our Client
    with Client(target) as client:
        # 1. Create a workcell
        workcell_name = "example_workcell"
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

        # 2. Add a robot system to the scene
        print("Add a system by connecting to the RDK and saving its configuration to the PDK server")
        system_name = "system_1"
        serial_number = "Rizon10s-2fZlcH"
        try:
            # Load the system from RDK
            add_system_response = client.system.stub.AddConnectedSystem(AddConnectedSystemRequest(name=system_name, serial_number=serial_number))

            if add_system_response.status.code == 0:
                print(f"Successfully added system: {system_name} with serial number: {serial_number}")
            else:
                print(f"Failed to add system: {system_name} with serial number: {serial_number}")

        except grpc.RpcError as e:
            print(f"System operation failed: {e}")

        # 3. Set the pose of the robot system in the scene
        print("Get system_1 and set its pose in the scene...")
        try:
            system_response = client.config.stub.Get(
                TypeNameConfigRequest(type=ConfigType.CONFIG_TYPE_SYSTEM, name=system_name)
            )
            if system_response.status.code == 0:
                system = system_response.system
                system.header.pose_in_parent.position.x = 0.73
                system.header.pose_in_parent.position.y = -1.7655
                system.header.pose_in_parent.position.z = 0.5

                # Save the updated system configuration to the PDK server
                save_response = client.config.stub.Save(SaveConfigRequest(system=system))
                if save_response.status.code == 0:
                    print(f"Successfully set pose for system: {system_name}")
                else:
                    print(f"Failed to set pose for system: {system_name}")
            else:
                print(f"Failed to get system: {system_name}")
        except grpc.RpcError as e:
            print(f"System operation failed: {e}")

        # 4. Add a camera to the scene
        print("Saving camera to the scene...")
        camera = Camera(
            header=make_header("camera_1", parent="system_1.arm.flange", px=-0.1, py=0.0, pz=0.0, rw=0.707107, rx=0.0, ry=0.0, rz=-0.707107),
            far_width=1.0,
            far_height=1.0,
            far_distance=2.0,
            near_distance=0.1,
            depth_scale=1000.0,
            camera_id=9
        )
        try:
            client.config.stub.Save(SaveConfigRequest(camera=camera))
        except grpc.RpcError:
            pass

        # 5. Check whether the camera is online
        print("Checking if the camera is online...")
        try:
            response = client.camera.stub.IsCameraOnline(CameraNameRequest(camera_name="camera_1"))
            print(f"Camera online: {response.online}")
        except grpc.RpcError as e:
            print(f"Camera online check failed or environment not running a server yet: {e}")
            return

        # 6. Add a reconstruction config
        print("Adding reconstruction config...")
        reconstruction_config_name = "example_reconstruction_config"
        reconstruction_config = ReconstructionConfig(
            name=reconstruction_config_name,
            point_cloud_size=1000000,
            voxel_size=0.005,
            voxel_bucket_count=10000,
        )
        try:
            status = client.reconstruction.stub.AddReconstructionConfig(reconstruction_config)
            if status.code != 0:
                print(f"Failed to add reconstruction config: {status.message}")
                return
        except grpc.RpcError as e:
            print(f"Add reconstruction config failed: {e}")
            return

        # Run a reconstruction using the camera
        print("Starting reconstruction...")
        try:
            status = client.reconstruction.stub.StartReconstruction(
                StartReconstructionRequest(
                    result_format="mesh",
                    publish_frequency=1.0,
                    reconstruction_config_name=reconstruction_config_name,
                )
            )
            if status.code != 0:
                print(f"Failed to start reconstruction: {status.message}")
                return
        except grpc.RpcError as e:
            print(f"Start reconstruction failed: {e}")
            return

        print("Adding camera to reconstruction...")
        try:
            status = client.reconstruction.stub.AddCameraToReconstruction(
                CameraNamesRequest(camera_names=["camera_1"])
            )
            if status.code != 0:
                print(f"Failed to add camera to reconstruction: {status.message}")
                return
        except grpc.RpcError as e:
            print(f"Add camera to reconstruction failed: {e}")
            return

        print("Fetching reconstruction result...")
        counter = 0
        while counter < 20:
            try:
                result = client.reconstruction.stub.GetReconstructionResult(
                    ReconstructionResultRequest(
                        header=make_header("example_reconstruction"),
                        add_to_scene=True,
                        replace_existing_object=True,
                    )
                )
                if result.status.code != 0:
                    print(f"Failed to get reconstruction result: {result.status.message}")
                else:
                    print("Reconstruction result saved successfully")
            except grpc.RpcError as e:
                print(f"Get reconstruction result failed: {e}")
                break
            counter+=1
            time.sleep(1)

        print("Listing available reconstruction objects...")
        try:
            response = client.reconstruction.stub.ListReconstructionObjects(empty_pb2.Empty())
            if response.status.code != 0:
                print(f"Failed to list reconstruction objects: {response.status.message}")
            else:
                for obj in response.objects:
                    print(f"  - {obj.name} ({obj.result_format})")
        except grpc.RpcError as e:
            print(f"List reconstruction objects failed: {e}")

        print("Removing camera from reconstruction...")
        try:
            status = client.reconstruction.stub.RemoveCameraFromReconstruction(
                CameraNamesRequest(camera_names=["camera_1"])
            )
            if status.code != 0:
                print(f"Failed to remove camera from reconstruction: {status.message}")
        except grpc.RpcError as e:
            print(f"Remove camera from reconstruction failed: {e}")

        print("Stopping reconstruction...")
        try:
            client.reconstruction.stub.StopReconstruction(empty_pb2.Empty())
        except grpc.RpcError as e:
            print(f"Stop reconstruction failed: {e}")

        print("Removing reconstruction config...")
        try:
            status = client.reconstruction.stub.RemoveReconstructionConfig(reconstruction_config)
            if status.code != 0:
                print(f"Failed to remove reconstruction config: {status.message}")
        except grpc.RpcError as e:
            print(f"Remove reconstruction config failed: {e}")


if __name__ == "__main__":
    main()
