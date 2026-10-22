"""
Example: Create a simple camera setup using the Flexiv PDK and fetch its data.

Note: To run this example, you need to have a Flexiv robot system with RDK remote mode enabled, and a camera with CAMID 9 enabled in the AIConsole in Noema Edge.
Modify the robot serial number and camera ID in the code below to match your setup. If the camera is a global camera, you should set the parent of the camera to "world" instead of "system_1.arm.flange".

This script demonstrates how to:
  1. Create a new workcell
  2. Add a robot system to the scene
  3. Add a camera to the scene
  4. Check whether the camera is online
  5. Save the camera's RGB and depth image to disk
  6. Save the camera's point cloud to disk
  7. List saved images and point clouds for the camera
"""
import os
import grpc
import time

from flexiv.pdk import Client
from flexiv.pdk.workcell.workcell_service_pb2 import CreateRequest, NameRequest
from flexiv.pdk.camera.service_pb2 import (
    CameraNameRequest,
    CameraRGBDImageRequest,
    CameraPointCloudRequest,
    CameraImageDeleteRequest,
    CameraPointCloudDeleteRequest,
)

from flexiv.pdk.config_service_pb2 import SaveConfigRequest, TypeNameConfigRequest, ConfigType
from flexiv.pdk.scene.camera_pb2 import Camera
from flexiv.pdk.config_header_pb2 import ConfigHeader
from flexiv.pdk.spatial.geometry_pb2 import SE3Pose, Vector3, Quaternion

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
        camera_name = "camera_1"
        camera = Camera(
            header=make_header(camera_name, parent="system_1.arm.flange", px=-0.1, py=0.0, pz=0.0, rw=0.707107, rx=0.0, ry=0.0, rz=-0.707107),
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
            response = client.camera.stub.IsCameraOnline(CameraNameRequest(camera_name=camera_name))
            print(f"Camera online: {response.online}")
            if not response.online:
                return
        except grpc.RpcError as e:
            print(f"Camera online check failed or environment not running a server yet: {e}")
            return
        
        # 6. Update camera intrinsics from device
        print("Updating camera intrinsics from device...")
        try:
            update_response = client.camera.stub.UpdateCameraIntrinsicFromDevice(CameraNameRequest(camera_name=camera_name))
            if update_response.status.code == 0:
                print(f"Successfully updated camera intrinsics for: {camera_name}")
            else:
                print(f"Failed to update camera intrinsics for: {camera_name}")
        except grpc.RpcError as e:
            print(f"Update camera intrinsics failed: {e}")
            return

        # 7. Save the camera's RGB and depth image to disk
        print("Saving camera RGBD image...")
        image_file_name = "example_rgbd_image"
        try:
            rgbd_response = client.camera.stub.GetCameraRGBDImage(
                CameraRGBDImageRequest(camera_name=camera_name, save_file_name=image_file_name)
            )
            if rgbd_response.status.code == 0:
                print(f"Saved RGBD image as: {image_file_name}")
            else:
                print(f"Failed to get RGBD image: {rgbd_response.status.message}")
        except grpc.RpcError as e:
            print(f"Get camera RGBD image failed: {e}")

        time.sleep(1)  # Wait a moment to ensure the image is saved before listing

        # 8. Save the camera's point cloud to disk
        print("Saving camera point cloud...")
        point_cloud_file_name = "example_point_cloud"
        try:
            pcd_response = client.camera.stub.GetCameraPointCloud(
                CameraPointCloudRequest(
                    camera_name=camera_name, in_world_frame=True, save_file_name=point_cloud_file_name
                )
            )
            if pcd_response.status.code == 0:
                print(f"Saved point cloud as: {point_cloud_file_name}")
            else:
                print(f"Failed to get point cloud: {pcd_response.status.message}")
        except grpc.RpcError as e:
            print(f"Get camera point cloud failed: {e}")

        # 9. List saved images and point clouds for the camera
        print("Listing saved camera images...")
        try:
            image_list_response = client.camera.stub.ListSavedCameraImages(CameraNameRequest(camera_name=camera_name))
            if image_list_response.status.code == 0:
                for image_file in image_list_response.image_file_names:
                    print(f"  - {image_file}")
            else:
                print(f"Failed to list saved camera images: {image_list_response.status.message}")
        except grpc.RpcError as e:
            print(f"List saved camera images failed: {e}")

        print("Listing saved camera point clouds...")
        try:
            pcd_list_response = client.camera.stub.ListSavedCameraPointClouds(CameraNameRequest(camera_name=camera_name))
            if pcd_list_response.status.code == 0:
                for point_cloud_file in pcd_list_response.point_cloud_file_names:
                    print(f"  - {point_cloud_file}")
            else:
                print(f"Failed to list saved camera point clouds: {pcd_list_response.status.message}")
        except grpc.RpcError as e:
            print(f"List saved camera point clouds failed: {e}")



if __name__ == "__main__":
    main()
