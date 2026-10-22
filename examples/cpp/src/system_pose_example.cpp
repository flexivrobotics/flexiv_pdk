/**
 * @file system_pose_example.cpp
 * @brief Example: Create system pose target waypoints from forward kinematics and use them to plan
 * a point-to-point path.
 *
 * This program demonstrates how to:
 *   1. Create a new workcell
 *   2. Add a robot system to the scene
 *   3. Compute forward kinematics for a joint configuration and save the result as a system pose
 *      target waypoint attached to the system
 *   4. Retrieve a saved system pose target waypoint from the scene
 *   5. Create a collision configuration, required by the point-to-point path service
 *   6. Run a point-to-point path plan referencing saved system pose target waypoints by name
 *
 * Needs a point_to_point_path license.
 */

#include <flexiv/pdk/client.hpp>
#include <flexiv/pdk/config_header.pb.h>
#include <flexiv/pdk/config_service.pb.h>
#include <flexiv/pdk/point_to_point_path/service.pb.h>
#include <flexiv/pdk/scene/collision/collision_service.pb.h>
#include <flexiv/pdk/scene/target_waypoint.pb.h>
#include <flexiv/pdk/system/components/manipulator.pb.h>
#include <flexiv/pdk/system/kinematics_service.pb.h>
#include <flexiv/pdk/system/system.pb.h>
#include <flexiv/pdk/workcell/workcell_service.pb.h>

#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

using flexiv::pdk::Client;
using flexiv::pdk::ConfigHeader;
using flexiv::pdk::common::Status;
using flexiv::pdk::spatial::SE3Pose;

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

// Computes the pose of system_1's flange for the given joint positions.
SE3Pose ComputeFlangePose(Client& client, const std::vector<double>& joint_positions)
{
  flexiv::pdk::system::FKRequest request;
  request.set_system_name("system_1");
  request.set_target_frame_name("system_1.arm.flange");
  for (double joint : joint_positions) {
    request.add_joint_positions(joint);
  }

  grpc::ClientContext context;
  flexiv::pdk::system::FKResponse response;
  const grpc::Status status = client.kinematics().stub->ComputeFK(&context, request, &response);
  if (!status.ok()) {
    std::cerr << "Kinematics error: " << status.error_message() << std::endl;
  } else {
    std::cout << "---------------------------------" << std::endl;
  }
  return response.pose();
}

// Saves a system pose target waypoint attached to system_1.
void SaveSystemPose(Client& client, const std::string& name, const SE3Pose& pose,
    const std::vector<double>& joint_positions)
{
  std::cout << "Saving system pose object to the scene..." << std::endl;
  flexiv::pdk::SaveConfigRequest request;
  auto* system_pose = request.mutable_system_pose();
  *system_pose->mutable_header() = MakeHeader(name, "system_1");
  system_pose->set_tcp_name("system_1.arm.flange");
  *system_pose->mutable_cartesian()->mutable_pose() = pose;
  for (double joint : joint_positions) {
    system_pose->mutable_joint()->add_position(joint);
  }

  grpc::ClientContext context;
  flexiv::pdk::SaveConfigResponse response;
  const grpc::Status status = client.config().stub->Save(&context, request, &response);
  if (!status.ok()) {
    std::cerr << "Save system pose object failed: " << status.error_message() << std::endl;
  }
}

} // namespace

int main()
{
  const std::string target = ServerAddress();
  std::cout << "Connecting to the PDK server at " << target << "..." << std::endl;

  Client client(target);
  const std::string workcell_name = "example_workcell";

  // 1. Remove any existing workcell
  std::cout << "Removing any existing workcell with name: " << workcell_name << std::endl;
  {
    grpc::ClientContext context;
    flexiv::pdk::workcell::NameRequest request;
    flexiv::pdk::workcell::RemoveResponse response;
    request.set_name(workcell_name);
    const grpc::Status status = client.workcell().stub->Remove(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Remove workcell failed or not present: " << status.error_message() << std::endl;
    }
  }

  // 2. Create a workcell
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

  // 3. Add a robot system to the scene
  std::cout << "Saving robot system to the scene..." << std::endl;
  {
    flexiv::pdk::SaveConfigRequest request;
    auto* system = request.mutable_system();
    *system->mutable_header() = MakeHeader("system_1");
    system->set_control_box_serial_number("CX01-01-T1-000001");
    system->mutable_manipulator()->set_name("arm");
    system->mutable_manipulator()->set_arm_serial_number("A02L-00-M3-000001");

    grpc::ClientContext context;
    flexiv::pdk::SaveConfigResponse response;
    client.config().stub->Save(&context, request, &response);
  }

  // 4. Run a forward kinematics on the first joint configuration
  const std::vector<double> joint_configuration_1 = {1.0, 0.4, 0.3, 1.5708, 0.5, 0.4, 0.0};
  const SE3Pose fk_pose_1 = ComputeFlangePose(client, joint_configuration_1);

  // 5. Add a system pose object to the scene, attached to system_1
  SaveSystemPose(client, "system_pose_1", fk_pose_1, joint_configuration_1);

  // 6. Get the system pose object back from the server to verify it was saved and can be retrieved
  std::cout << "Retrieving system pose object from the scene..." << std::endl;
  {
    flexiv::pdk::TypeNameConfigRequest request;
    request.set_type(flexiv::pdk::CONFIG_TYPE_SYSTEM_POSE);
    request.set_name("system_pose_1");

    grpc::ClientContext context;
    flexiv::pdk::GetConfigResponse response;
    const grpc::Status status = client.config().stub->Get(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Get system pose object failed: " << status.error_message() << std::endl;
    } else {
      std::cout << "Retrieved system pose object: " << response.system_pose().DebugString()
                << std::endl;
    }
  }

  // 7. Run a forward kinematics on the second joint configuration
  const std::vector<double> joint_configuration_2 = {1.0, 0.4, 0.3, 0.0, 0.5, 0.4, 0.0};
  const SE3Pose fk_pose_2 = ComputeFlangePose(client, joint_configuration_2);

  // 8. Add a system pose object to the scene, attached to system_1
  SaveSystemPose(client, "system_pose_2", fk_pose_2, joint_configuration_2);

  // 9. Create a default collision configuration, required by the point-to-point path service
  std::cout << "Creating default collision configuration..." << std::endl;
  {
    flexiv::pdk::scene::collision::SaveRequest request;
    request.mutable_collision_config()->set_name("default_collision_config");

    grpc::ClientContext context;
    flexiv::pdk::scene::collision::SaveResponse response;
    const grpc::Status status = client.collision().stub->Save(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Save collision config failed: " << status.error_message() << std::endl;
    }
  }

  // 10. Run a point-to-point path plan directly from the saved system pose target waypoints
  std::cout << "Running point-to-point path plan using the system pose target waypoints..."
            << std::endl;
  {
    flexiv::pdk::point_to_point_path::PointToPointPathRequest request;
    request.set_path_name("ptp_path_system_pose_1");
    request.set_collision_config_name("default_collision_config");
    request.mutable_target_waypoints()->add_target_waypoint_names("system_pose_1");
    request.mutable_target_waypoints()->add_target_waypoint_names("system_pose_2");

    grpc::ClientContext context;
    flexiv::pdk::point_to_point_path::PointToPointPathResponse response;
    const grpc::Status status
        = client.point_to_point_path().stub->Plan(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Point-to-point path plan failed: " << status.error_message() << std::endl;
    } else if (response.status().code() == Status::OK) {
      std::cout << "Point-to-point path plan successful" << std::endl;
    } else {
      std::cout << "Point-to-point path plan failed: " << response.status().message() << std::endl;
    }
  }

  return 0;
}
