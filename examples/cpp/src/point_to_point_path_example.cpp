/**
 * @file point_to_point_path_example.cpp
 * @brief Example: Create a simple scene and run point-to-point path planning queries using the
 * Flexiv PDK.
 *
 * This program demonstrates how to:
 *   1. Create a new workcell
 *   2. Add multiple objects to the scene
 *   3. Add one robot system to the scene
 *   4. Create collision configurations
 *   5. Run point-to-point path planning queries with different collision configurations
 *
 * Needs a point_to_point_path license.
 */

#include <flexiv/pdk/client.hpp>
#include <flexiv/pdk/config_header.pb.h>
#include <flexiv/pdk/config_service.pb.h>
#include <flexiv/pdk/point_to_point_path/path.pb.h>
#include <flexiv/pdk/point_to_point_path/service.pb.h>
#include <flexiv/pdk/scene/collision/collision_config.pb.h>
#include <flexiv/pdk/scene/collision/collision_service.pb.h>
#include <flexiv/pdk/scene/object.pb.h>
#include <flexiv/pdk/spatial/waypoint.pb.h>
#include <flexiv/pdk/system/system.pb.h>
#include <flexiv/pdk/workcell/workcell_service.pb.h>

#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <utility>
#include <vector>

using flexiv::pdk::Client;
using flexiv::pdk::ConfigHeader;
using flexiv::pdk::common::Status;
using flexiv::pdk::scene::Object;
using flexiv::pdk::system::System;

namespace {

constexpr double kDegToRad = 3.14159265358979323846 / 180.0;

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

Object MakeBox(const std::string& name, const std::string& parent, double px, double py, double pz,
    double size_x, double size_y, double size_z)
{
  Object object;
  *object.mutable_header() = MakeHeader(name, parent, px, py, pz);

  auto* visual = object.add_visual();
  visual->mutable_origin()->mutable_rotation()->set_w(1.0);
  auto* visual_box = visual->mutable_shape()->mutable_box();
  visual_box->add_size(size_x);
  visual_box->add_size(size_y);
  visual_box->add_size(size_z);

  auto* collision = object.add_collision();
  *collision->mutable_origin() = visual->origin();
  *collision->mutable_shape() = visual->shape();
  return object;
}

System CreateSystem(const std::string& name, const std::string& arm_serial_number,
    const std::string& control_box_serial_number, double px, double py, double pz)
{
  System system;
  *system.mutable_header() = MakeHeader(name, "world", px, py, pz);
  system.set_control_box_serial_number(control_box_serial_number);

  auto* adapter = system.mutable_manipulator_adapter();
  adapter->set_name("manipulator_adapter");
  adapter->set_mass(0.0);
  for (int i = 0; i < 9; ++i) {
    adapter->add_inertia(0.0);
  }
  for (int i = 0; i < 3; ++i) {
    adapter->add_xyz(0.0);
    adapter->add_rpy(0.0);
  }

  auto* manipulator = system.mutable_manipulator();
  manipulator->set_name("arm");
  manipulator->set_arm_serial_number(arm_serial_number);
  for (int i = 0; i < 7; ++i) {
    manipulator->add_lower_limit(-2.76);
    manipulator->add_upper_limit(2.76);
    manipulator->add_home_position(0.0);
  }
  return system;
}

void SaveCollisionConfig(Client& client, const std::string& name,
    const std::vector<std::pair<std::string, std::string>>& pairs, double collision_margin)
{
  flexiv::pdk::scene::collision::SaveRequest request;
  auto* config = request.mutable_collision_config();
  config->set_name(name);
  config->set_collision_margin(collision_margin);
  for (const auto& [name1, name2] : pairs) {
    auto* pair = config->add_pairs();
    pair->set_name1(name1);
    pair->set_name2(name2);
  }

  grpc::ClientContext context;
  flexiv::pdk::scene::collision::SaveResponse response;
  const grpc::Status status = client.collision().stub->Save(&context, request, &response);
  if (!status.ok()) {
    std::cerr << "Save collision config failed: " << status.error_message() << std::endl;
  }
}

// Prints the waypoints of a planned path, read back from the scene.
void PrintPath(Client& client, const std::string& path_name)
{
  flexiv::pdk::TypeNameConfigRequest request;
  request.set_name(path_name);
  request.set_type(flexiv::pdk::CONFIG_TYPE_P2P_PATH);

  grpc::ClientContext context;
  flexiv::pdk::GetConfigResponse response;
  const grpc::Status status = client.config().stub->Get(&context, request, &response);
  if (!status.ok()) {
    std::cerr << "  Failed to retrieve path: " << status.error_message() << std::endl;
    return;
  }
  if (response.status().code() != Status::OK || !response.has_p2p_path()) {
    std::cout << "  Failed to retrieve path: " << response.status().message() << std::endl;
    return;
  }

  const auto& path = response.p2p_path();
  std::cout << std::fixed << std::setprecision(4);
  std::cout << "  Cartesian waypoints (" << path.cartesian_waypoints_size() << "):" << std::endl;
  for (int i = 0; i < path.cartesian_waypoints_size(); ++i) {
    const auto& p = path.cartesian_waypoints(i).pose().position();
    const auto& q = path.cartesian_waypoints(i).pose().rotation();
    std::cout << "    [" << i << "] pos=(" << p.x() << ", " << p.y() << ", " << p.z() << ")  rot=("
              << q.x() << ", " << q.y() << ", " << q.z() << ", " << q.w() << ")" << std::endl;
  }
  std::cout << "  Joint waypoints (" << path.joint_waypoints_size() << "):" << std::endl;
  for (int i = 0; i < path.joint_waypoints_size(); ++i) {
    std::cout << "    [" << i << "] [";
    const auto& position = path.joint_waypoints(i).position();
    for (int j = 0; j < position.size(); ++j) {
      std::cout << (j > 0 ? ", " : "") << position[j];
    }
    std::cout << "]" << std::endl;
  }
  std::cout << std::defaultfloat;
}

void RunPlan(Client& client, const std::string& path_name, const std::string& system_name,
    const std::string& tcp_name, const std::string& collision_config_name,
    const std::vector<std::vector<double>>& joint_waypoints)
{
  flexiv::pdk::point_to_point_path::PointToPointPathRequest request;
  request.set_path_name(path_name);
  request.set_collision_config_name(collision_config_name);
  auto* waypoints = request.mutable_joint_waypoints();
  waypoints->set_system_name(system_name);
  waypoints->set_tcp_name(tcp_name);
  for (const auto& positions : joint_waypoints) {
    auto* waypoint = waypoints->add_joint_waypoints();
    for (double position : positions) {
      waypoint->add_position(position);
    }
  }

  grpc::ClientContext context;
  flexiv::pdk::point_to_point_path::PointToPointPathResponse response;
  const grpc::Status status = client.point_to_point_path().stub->Plan(&context, request, &response);
  if (!status.ok()) {
    std::cerr << "Plan failed: " << status.error_message() << std::endl;
    return;
  }
  std::cout << std::endl;
  if (response.status().code() == Status::OK) {
    std::cout << "Plan successful" << std::endl;
    PrintPath(client, path_name);
  } else {
    std::cout << "Plan failed with status code " << response.status().code() << ": "
              << response.status().message() << std::endl;
  }
}

} // namespace

int main()
{
  const std::string target = ServerAddress();
  const std::string workcell_name = "example_workcell";
  std::cout << "Connecting to the PDK server at " << target << "..." << std::endl;

  Client client(target);

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

  // 2. Create and load workcell
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
      std::cerr << "Workcell operation failed: " << status.error_message() << std::endl;
    }
  }

  // 3. Add one robot system to the scene
  std::cout << "Saving robot system to the scene..." << std::endl;
  {
    flexiv::pdk::SaveConfigRequest request;
    *request.mutable_system()
        = CreateSystem("system_1", "A02L-00-M3-000001", "CX01-01-T1-000001", 0.0, 0.0, 0.0);
    grpc::ClientContext context;
    flexiv::pdk::SaveConfigResponse response;
    const grpc::Status status = client.config().stub->Save(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Save system failed: " << status.error_message() << std::endl;
    }
  }

  std::cout << "Commands executed to create workcell, 3 objects, and 1 system in the scene!"
            << std::endl;

  // 4. Add objects to the environment, with one object attached to the system's flange
  std::cout << "Saving objects to the scene..." << std::endl;
  for (const Object& object : {
           MakeBox("box_1", "world", 0.5, 0.0, 0.0, 0.2, 0.2, 0.2),
           MakeBox("box_2", "world", 0.5, 0.5, 0.0, 0.2, 0.2, 0.2),
           MakeBox("box_3", "world", 0.5, 1.0, 0.0, 0.2, 0.2, 0.2),
           MakeBox("box_4", "system_1.arm.flange", 0.0, 0.0, 0.0251, 0.05, 0.05, 0.05),
       }) {
    flexiv::pdk::SaveConfigRequest request;
    *request.mutable_object() = object;
    grpc::ClientContext context;
    flexiv::pdk::SaveConfigResponse response;
    const grpc::Status status = client.config().stub->Save(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Save object failed: " << status.error_message() << std::endl;
    }
  }

  // 5. Collision configuration
  std::cout << "Creating collision configurations..." << std::endl;

  // Default collision configuration - no pairs are excluded
  SaveCollisionConfig(client, "default_collision_config", {}, 0.0);

  // Collision configuration that excludes collisions between system_1.arm and box_1
  SaveCollisionConfig(client, "collision_config_without_box_1", {{"system_1.arm", "box_1"}}, 0.0);

  // Collision configuration that excludes collisions between system_1.arm and box_1 and box 4 and
  // box 1
  SaveCollisionConfig(client, "collision_config_without_box_1_and_box_4",
      {{"system_1.arm", "box_1"}, {"box_4", "box_1"}}, 0.0);

  // 6. Point-to-point path planning queries
  std::cout << "Running point-to-point path planning queries..." << std::endl;
  const std::vector<double> home = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
  const std::vector<double> clear_goal
      = {0.0, -40.0 * kDegToRad, 0.0, 90.0 * kDegToRad, 0.0, 40.0 * kDegToRad, 0.0};
  const std::vector<double> box_1_goal = {13.24 * kDegToRad, -69.97 * kDegToRad, 0.06 * kDegToRad,
      112.91 * kDegToRad, 1.03 * kDegToRad, 92.89 * kDegToRad, 12.23 * kDegToRad};

  // 1. No collision
  RunPlan(client, "ptp_path_1", "system_1", "system_1.arm.flange", "default_collision_config",
      {home, clear_goal});
  // 2. With collision (between system_1.arm and box_1)
  RunPlan(client, "ptp_path_2", "system_1", "system_1.arm.flange", "default_collision_config",
      {home, box_1_goal});
  // 3. With collision (between box_4 and box_1)
  RunPlan(client, "ptp_path_3", "system_1", "system_1.arm.flange", "collision_config_without_box_1",
      {home, box_1_goal});
  // 4. No collision
  RunPlan(client, "ptp_path_4", "system_1", "system_1.arm.flange",
      "collision_config_without_box_1_and_box_4", {home, box_1_goal});

  std::cout << "All scene setup and planning queries complete." << std::endl;
  return 0;
}
