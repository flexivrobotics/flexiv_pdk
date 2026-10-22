/**
 * @file camera_example.cpp
 * @brief Example: Create a simple camera setup using the Flexiv PDK and fetch its data.
 *
 * Note: To run this example, you need to have a Flexiv robot system with RDK remote mode enabled,
 * and a camera with CAMID 9 enabled in the AIConsole in Noema Edge. Modify the robot serial number
 * and camera ID in the code below to match your setup. If the camera is a global camera, you
 * should set the parent of the camera to "world" instead of "system_1.arm.flange".
 *
 * This program demonstrates how to:
 *   1. Create a new workcell
 *   2. Add a robot system to the scene
 *   3. Add a camera to the scene
 *   4. Check whether the camera is online
 *   5. Save the camera's RGB and depth image to disk
 *   6. Save the camera's point cloud to disk
 *   7. List saved images and point clouds for the camera
 */

#include <flexiv/pdk/camera/service.pb.h>
#include <flexiv/pdk/client.hpp>
#include <flexiv/pdk/config_header.pb.h>
#include <flexiv/pdk/config_service.pb.h>
#include <flexiv/pdk/scene/camera.pb.h>
#include <flexiv/pdk/system/system.pb.h>
#include <flexiv/pdk/system/system_service.pb.h>
#include <flexiv/pdk/workcell/workcell_service.pb.h>

#include <chrono>
#include <cstdlib>
#include <iostream>
#include <string>
#include <thread>

using flexiv::pdk::Client;
using flexiv::pdk::ConfigHeader;
using flexiv::pdk::camera::CameraNameRequest;
using flexiv::pdk::common::Status;

namespace {

std::string ServerAddress()
{
  const char* address = std::getenv("PDK_SERVER_ADDR");
  return address != nullptr ? address : "localhost:50052";
}

ConfigHeader MakeHeader(const std::string& name, const std::string& parent = "world",
    double px = 0.0, double py = 0.0, double pz = 0.0, double rw = 1.0, double rx = 0.0,
    double ry = 0.0, double rz = 0.0)
{
  ConfigHeader header;
  header.set_name(name);
  header.set_parent(parent);
  auto* pose = header.mutable_pose_in_parent();
  pose->mutable_position()->set_x(px);
  pose->mutable_position()->set_y(py);
  pose->mutable_position()->set_z(pz);
  pose->mutable_rotation()->set_w(rw);
  pose->mutable_rotation()->set_x(rx);
  pose->mutable_rotation()->set_y(ry);
  pose->mutable_rotation()->set_z(rz);
  return header;
}

} // namespace

int main()
{
  const std::string target = ServerAddress();
  std::cout << "Connecting to the PDK server at " << target << "..." << std::endl;

  Client client(target);

  // 1. Create a workcell
  const std::string workcell_name = "example_workcell";
  std::cout << "Creating workcell: " << workcell_name << std::endl;
  {
    grpc::ClientContext create_context;
    flexiv::pdk::workcell::CreateRequest create_request;
    flexiv::pdk::workcell::CreateResponse create_response;
    create_request.set_name(workcell_name);
    create_request.set_description("A dual-robot setup with objects");
    grpc::Status status
        = client.workcell().stub->Create(&create_context, create_request, &create_response);
    if (status.ok()) {
      grpc::ClientContext load_context;
      flexiv::pdk::workcell::NameRequest load_request;
      flexiv::pdk::workcell::WorkcellResponse load_response;
      load_request.set_name(workcell_name);
      status = client.workcell().stub->Load(&load_context, load_request, &load_response);
    }
    if (!status.ok()) {
      std::cerr << "Workcell operation failed or environment not running a server yet: "
                << status.error_message() << std::endl;
    }
  }

  // 2. Add a robot system to the scene
  std::cout << "Add a system by connecting to the RDK and saving its configuration to the PDK "
               "server"
            << std::endl;
  const std::string system_name = "system_1";
  const std::string serial_number = "Rizon10s-2fZlcH";
  {
    flexiv::pdk::system::AddConnectedSystemRequest request;
    request.set_name(system_name);
    request.set_serial_number(serial_number);

    grpc::ClientContext context;
    flexiv::pdk::system::AddConnectedSystemResponse response;
    const grpc::Status status
        = client.system().stub->AddConnectedSystem(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "System operation failed: " << status.error_message() << std::endl;
    } else if (response.status().code() == Status::OK) {
      std::cout << "Successfully added system: " << system_name
                << " with serial number: " << serial_number << std::endl;
    } else {
      std::cout << "Failed to add system: " << system_name
                << " with serial number: " << serial_number << std::endl;
    }
  }

  // 3. Set the pose of the robot system in the scene
  std::cout << "Get system_1 and set its pose in the scene..." << std::endl;
  {
    flexiv::pdk::TypeNameConfigRequest get_request;
    get_request.set_type(flexiv::pdk::CONFIG_TYPE_SYSTEM);
    get_request.set_name(system_name);

    grpc::ClientContext get_context;
    flexiv::pdk::GetConfigResponse get_response;
    grpc::Status status = client.config().stub->Get(&get_context, get_request, &get_response);
    if (!status.ok()) {
      std::cerr << "System operation failed: " << status.error_message() << std::endl;
    } else if (get_response.status().code() != Status::OK) {
      std::cout << "Failed to get system: " << system_name << std::endl;
    } else {
      flexiv::pdk::SaveConfigRequest save_request;
      auto* system = save_request.mutable_system();
      *system = get_response.system();
      auto* position = system->mutable_header()->mutable_pose_in_parent()->mutable_position();
      position->set_x(0.73);
      position->set_y(-1.7655);
      position->set_z(0.5);

      // Save the updated system configuration to the PDK server
      grpc::ClientContext save_context;
      flexiv::pdk::SaveConfigResponse save_response;
      status = client.config().stub->Save(&save_context, save_request, &save_response);
      if (!status.ok()) {
        std::cerr << "System operation failed: " << status.error_message() << std::endl;
      } else if (save_response.status().code() == Status::OK) {
        std::cout << "Successfully set pose for system: " << system_name << std::endl;
      } else {
        std::cout << "Failed to set pose for system: " << system_name << std::endl;
      }
    }
  }

  // 4. Add a camera to the scene
  std::cout << "Saving camera to the scene..." << std::endl;
  const std::string camera_name = "camera_1";
  {
    flexiv::pdk::SaveConfigRequest request;
    auto* camera = request.mutable_camera();
    *camera->mutable_header() = MakeHeader(
        camera_name, "system_1.arm.flange", -0.1, 0.0, 0.0, 0.707107, 0.0, 0.0, -0.707107);
    camera->set_far_width(1.0);
    camera->set_far_height(1.0);
    camera->set_far_distance(2.0);
    camera->set_near_distance(0.1);
    camera->set_depth_scale(1000.0);
    camera->set_camera_id(9);

    grpc::ClientContext context;
    flexiv::pdk::SaveConfigResponse response;
    client.config().stub->Save(&context, request, &response);
  }

  CameraNameRequest camera_request;
  camera_request.set_camera_name(camera_name);

  // 5. Check whether the camera is online
  std::cout << "Checking if the camera is online..." << std::endl;
  {
    grpc::ClientContext context;
    flexiv::pdk::camera::CameraOnlineResponse response;
    const grpc::Status status
        = client.camera().stub->IsCameraOnline(&context, camera_request, &response);
    if (!status.ok()) {
      std::cerr << "Camera online check failed or environment not running a server yet: "
                << status.error_message() << std::endl;
      return 1;
    }
    std::cout << "Camera online: " << std::boolalpha << response.online() << std::endl;
    if (!response.online()) {
      return 1;
    }
  }

  // 6. Update camera intrinsics from device
  std::cout << "Updating camera intrinsics from device..." << std::endl;
  {
    grpc::ClientContext context;
    flexiv::pdk::camera::UpdateCameraIntrinsicFromDeviceResponse response;
    const grpc::Status status = client.camera().stub->UpdateCameraIntrinsicFromDevice(
        &context, camera_request, &response);
    if (!status.ok()) {
      std::cerr << "Update camera intrinsics failed: " << status.error_message() << std::endl;
      return 1;
    }
    if (response.status().code() == Status::OK) {
      std::cout << "Successfully updated camera intrinsics for: " << camera_name << std::endl;
    } else {
      std::cout << "Failed to update camera intrinsics for: " << camera_name << std::endl;
    }
  }

  // 7. Save the camera's RGB and depth image to disk
  std::cout << "Saving camera RGBD image..." << std::endl;
  const std::string image_file_name = "example_rgbd_image";
  {
    flexiv::pdk::camera::CameraRGBDImageRequest request;
    request.set_camera_name(camera_name);
    request.set_save_file_name(image_file_name);

    grpc::ClientContext context;
    flexiv::pdk::camera::CameraRGBDImageResponse response;
    const grpc::Status status
        = client.camera().stub->GetCameraRGBDImage(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Get camera RGBD image failed: " << status.error_message() << std::endl;
    } else if (response.status().code() == Status::OK) {
      std::cout << "Saved RGBD image as: " << image_file_name << std::endl;
    } else {
      std::cout << "Failed to get RGBD image: " << response.status().message() << std::endl;
    }
  }

  // Wait a moment to ensure the image is saved before listing
  std::this_thread::sleep_for(std::chrono::seconds(1));

  // 8. Save the camera's point cloud to disk
  std::cout << "Saving camera point cloud..." << std::endl;
  const std::string point_cloud_file_name = "example_point_cloud";
  {
    flexiv::pdk::camera::CameraPointCloudRequest request;
    request.set_camera_name(camera_name);
    request.set_in_world_frame(true);
    request.set_save_file_name(point_cloud_file_name);

    grpc::ClientContext context;
    flexiv::pdk::camera::CameraPointCloudResponse response;
    const grpc::Status status
        = client.camera().stub->GetCameraPointCloud(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Get camera point cloud failed: " << status.error_message() << std::endl;
    } else if (response.status().code() == Status::OK) {
      std::cout << "Saved point cloud as: " << point_cloud_file_name << std::endl;
    } else {
      std::cout << "Failed to get point cloud: " << response.status().message() << std::endl;
    }
  }

  // 9. List saved images and point clouds for the camera
  std::cout << "Listing saved camera images..." << std::endl;
  {
    grpc::ClientContext context;
    flexiv::pdk::camera::CameraImageListResponse response;
    const grpc::Status status
        = client.camera().stub->ListSavedCameraImages(&context, camera_request, &response);
    if (!status.ok()) {
      std::cerr << "List saved camera images failed: " << status.error_message() << std::endl;
    } else if (response.status().code() == Status::OK) {
      for (const auto& image_file : response.image_file_names()) {
        std::cout << "  - " << image_file << std::endl;
      }
    } else {
      std::cout << "Failed to list saved camera images: " << response.status().message()
                << std::endl;
    }
  }

  std::cout << "Listing saved camera point clouds..." << std::endl;
  {
    grpc::ClientContext context;
    flexiv::pdk::camera::CameraPointCloudListResponse response;
    const grpc::Status status
        = client.camera().stub->ListSavedCameraPointClouds(&context, camera_request, &response);
    if (!status.ok()) {
      std::cerr << "List saved camera point clouds failed: " << status.error_message() << std::endl;
    } else if (response.status().code() == Status::OK) {
      for (const auto& point_cloud_file : response.point_cloud_file_names()) {
        std::cout << "  - " << point_cloud_file << std::endl;
      }
    } else {
      std::cout << "Failed to list saved camera point clouds: " << response.status().message()
                << std::endl;
    }
  }

  return 0;
}
