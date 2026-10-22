/**
 * @file reconstruction_example.cpp
 * @brief Example: Run a reconstruction using the Flexiv PDK.
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
 *   5. Add a reconstruction config
 *   6. Run a reconstruction using the camera and the config
 *   7. List available reconstruction objects
 *   8. Remove the camera from the reconstruction
 *   9. Remove the reconstruction config
 */

#include <flexiv/pdk/camera/service.pb.h>
#include <flexiv/pdk/client.hpp>
#include <flexiv/pdk/config_header.pb.h>
#include <flexiv/pdk/config_service.pb.h>
#include <flexiv/pdk/scene/camera.pb.h>
#include <flexiv/pdk/scene/reconstruction/config.pb.h>
#include <flexiv/pdk/scene/reconstruction/service.pb.h>
#include <flexiv/pdk/system/system.pb.h>
#include <flexiv/pdk/system/system_service.pb.h>
#include <flexiv/pdk/workcell/workcell_service.pb.h>
#include <google/protobuf/empty.pb.h>

#include <chrono>
#include <cstdlib>
#include <iostream>
#include <string>
#include <thread>

using flexiv::pdk::Client;
using flexiv::pdk::ConfigHeader;
using flexiv::pdk::common::Status;
using flexiv::pdk::scene::reconstruction::CameraNamesRequest;
using flexiv::pdk::scene::reconstruction::ReconstructionConfig;

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
  {
    flexiv::pdk::SaveConfigRequest request;
    auto* camera = request.mutable_camera();
    *camera->mutable_header() = MakeHeader(
        "camera_1", "system_1.arm.flange", -0.1, 0.0, 0.0, 0.707107, 0.0, 0.0, -0.707107);
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

  // 5. Check whether the camera is online
  std::cout << "Checking if the camera is online..." << std::endl;
  {
    flexiv::pdk::camera::CameraNameRequest request;
    request.set_camera_name("camera_1");

    grpc::ClientContext context;
    flexiv::pdk::camera::CameraOnlineResponse response;
    const grpc::Status status = client.camera().stub->IsCameraOnline(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Camera online check failed or environment not running a server yet: "
                << status.error_message() << std::endl;
      return 1;
    }
    std::cout << "Camera online: " << std::boolalpha << response.online() << std::endl;
  }

  // 6. Add a reconstruction config
  std::cout << "Adding reconstruction config..." << std::endl;
  const std::string reconstruction_config_name = "example_reconstruction_config";
  ReconstructionConfig reconstruction_config;
  reconstruction_config.set_name(reconstruction_config_name);
  reconstruction_config.set_point_cloud_size(1000000);
  reconstruction_config.set_voxel_size(0.005);
  reconstruction_config.set_voxel_bucket_count(10000);
  {
    grpc::ClientContext context;
    Status response;
    const grpc::Status status = client.reconstruction().stub->AddReconstructionConfig(
        &context, reconstruction_config, &response);
    if (!status.ok()) {
      std::cerr << "Add reconstruction config failed: " << status.error_message() << std::endl;
      return 1;
    }
    if (response.code() != Status::OK) {
      std::cout << "Failed to add reconstruction config: " << response.message() << std::endl;
      return 1;
    }
  }

  // Run a reconstruction using the camera
  std::cout << "Starting reconstruction..." << std::endl;
  {
    flexiv::pdk::scene::reconstruction::StartReconstructionRequest request;
    request.set_result_format("mesh");
    request.set_publish_frequency(1.0);
    request.set_reconstruction_config_name(reconstruction_config_name);

    grpc::ClientContext context;
    Status response;
    const grpc::Status status
        = client.reconstruction().stub->StartReconstruction(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Start reconstruction failed: " << status.error_message() << std::endl;
      return 1;
    }
    if (response.code() != Status::OK) {
      std::cout << "Failed to start reconstruction: " << response.message() << std::endl;
      return 1;
    }
  }

  CameraNamesRequest camera_names;
  camera_names.add_camera_names("camera_1");

  std::cout << "Adding camera to reconstruction..." << std::endl;
  {
    grpc::ClientContext context;
    Status response;
    const grpc::Status status = client.reconstruction().stub->AddCameraToReconstruction(
        &context, camera_names, &response);
    if (!status.ok()) {
      std::cerr << "Add camera to reconstruction failed: " << status.error_message() << std::endl;
      return 1;
    }
    if (response.code() != Status::OK) {
      std::cout << "Failed to add camera to reconstruction: " << response.message() << std::endl;
      return 1;
    }
  }

  std::cout << "Fetching reconstruction result..." << std::endl;
  for (int counter = 0; counter < 20; ++counter) {
    flexiv::pdk::scene::reconstruction::ReconstructionResultRequest request;
    *request.mutable_header() = MakeHeader("example_reconstruction");
    request.set_add_to_scene(true);
    request.set_replace_existing_object(true);

    grpc::ClientContext context;
    flexiv::pdk::scene::reconstruction::ReconstructionResultResponse response;
    const grpc::Status status
        = client.reconstruction().stub->GetReconstructionResult(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Get reconstruction result failed: " << status.error_message() << std::endl;
      break;
    }
    if (response.status().code() != Status::OK) {
      std::cout << "Failed to get reconstruction result: " << response.status().message()
                << std::endl;
    } else {
      std::cout << "Reconstruction result saved successfully" << std::endl;
    }
    std::this_thread::sleep_for(std::chrono::seconds(1));
  }

  std::cout << "Listing available reconstruction objects..." << std::endl;
  {
    grpc::ClientContext context;
    flexiv::pdk::scene::reconstruction::ListReconstructionObjectsResponse response;
    const grpc::Status status = client.reconstruction().stub->ListReconstructionObjects(
        &context, google::protobuf::Empty(), &response);
    if (!status.ok()) {
      std::cerr << "List reconstruction objects failed: " << status.error_message() << std::endl;
    } else if (response.status().code() != Status::OK) {
      std::cout << "Failed to list reconstruction objects: " << response.status().message()
                << std::endl;
    } else {
      for (const auto& object : response.objects()) {
        std::cout << "  - " << object.name() << " (" << object.result_format() << ")" << std::endl;
      }
    }
  }

  std::cout << "Removing camera from reconstruction..." << std::endl;
  {
    grpc::ClientContext context;
    Status response;
    const grpc::Status status = client.reconstruction().stub->RemoveCameraFromReconstruction(
        &context, camera_names, &response);
    if (!status.ok()) {
      std::cerr << "Remove camera from reconstruction failed: " << status.error_message()
                << std::endl;
    } else if (response.code() != Status::OK) {
      std::cout << "Failed to remove camera from reconstruction: " << response.message()
                << std::endl;
    }
  }

  std::cout << "Stopping reconstruction..." << std::endl;
  {
    grpc::ClientContext context;
    Status response;
    const grpc::Status status = client.reconstruction().stub->StopReconstruction(
        &context, google::protobuf::Empty(), &response);
    if (!status.ok()) {
      std::cerr << "Stop reconstruction failed: " << status.error_message() << std::endl;
    }
  }

  std::cout << "Removing reconstruction config..." << std::endl;
  {
    grpc::ClientContext context;
    Status response;
    const grpc::Status status = client.reconstruction().stub->RemoveReconstructionConfig(
        &context, reconstruction_config, &response);
    if (!status.ok()) {
      std::cerr << "Remove reconstruction config failed: " << status.error_message() << std::endl;
    } else if (response.code() != Status::OK) {
      std::cout << "Failed to remove reconstruction config: " << response.message() << std::endl;
    }
  }

  return 0;
}
