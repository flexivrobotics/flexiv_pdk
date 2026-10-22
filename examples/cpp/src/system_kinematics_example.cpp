/**
 * @file system_kinematics_example.cpp
 * @brief Example: Create a simple scene with a robot system and compute forward and inverse
 * kinematics using the Flexiv PDK.
 *
 * This program demonstrates how to:
 *   1. Create a new workcell
 *   2. Add a robot system to the scene
 *   3. Save a collision configuration, required by inverse kinematics
 *   4. Compute forward kinematics for a joint configuration
 *   5. Compute inverse kinematics for the resulting pose, without and with a seed
 */

#include <flexiv/pdk/client.hpp>
#include <flexiv/pdk/config_header.pb.h>
#include <flexiv/pdk/config_service.pb.h>
#include <flexiv/pdk/scene/collision/collision_config.pb.h>
#include <flexiv/pdk/scene/collision/collision_service.pb.h>
#include <flexiv/pdk/system/components/manipulator.pb.h>
#include <flexiv/pdk/system/kinematics_service.pb.h>
#include <flexiv/pdk/system/system.pb.h>
#include <flexiv/pdk/workcell/workcell_service.pb.h>

#include <chrono>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

using flexiv::pdk::Client;
using flexiv::pdk::ConfigHeader;
using flexiv::pdk::spatial::SE3Pose;
using flexiv::pdk::system::FKRequest;
using flexiv::pdk::system::FKResponse;
using flexiv::pdk::system::IKRequest;
using flexiv::pdk::system::IKResponse;

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

double MillisecondsSince(std::chrono::steady_clock::time_point start)
{
  return std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - start)
      .count();
}

// Computes inverse kinematics for the flange of system_1, optionally from a seed, and prints it.
void ComputeIK(Client& client, const SE3Pose& target_pose, const std::string& collision_config_name,
    const std::vector<double>& seed)
{
  IKRequest request;
  request.set_system_name("system_1");
  request.set_target_frame_name("system_1.arm.flange");
  *request.mutable_target_pose() = target_pose;
  request.set_collision_config_name(collision_config_name);
  for (double joint : seed) {
    request.add_joint_position_seed(joint);
  }

  grpc::ClientContext context;
  IKResponse response;
  const auto start = std::chrono::steady_clock::now();
  const grpc::Status status = client.kinematics().stub->ComputeIK(&context, request, &response);
  const double elapsed_ms = MillisecondsSince(start);
  if (!status.ok()) {
    std::cerr << "Kinematics error: " << status.error_message() << std::endl;
    return;
  }
  std::cout << std::endl
            << "--- Inverse Kinematics Result (" << std::fixed << std::setprecision(2) << elapsed_ms
            << " ms) ---" << std::endl
            << std::defaultfloat << response.DebugString() << "---------------------------------"
            << std::endl;
}

} // namespace

int main()
{
  const std::string target = ServerAddress();
  std::cout << "Connecting to the PDK server at " << target << "..." << std::endl;

  Client client(target);
  const std::string workcell_name = "example_workcell";

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

  std::cout << "Creating workcell: " << workcell_name << std::endl;
  {
    grpc::ClientContext create_context;
    flexiv::pdk::workcell::CreateRequest create_request;
    flexiv::pdk::workcell::CreateResponse create_response;
    create_request.set_name(workcell_name);
    create_request.set_description("A single-robot setup for kinematics calculation");
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

  std::cout << "Saving robot system to the scene..." << std::endl;
  {
    flexiv::pdk::SaveConfigRequest request;
    auto* system = request.mutable_system();
    *system->mutable_header() = MakeHeader("system_1", "world", -0.7, 0.0, 0.0);
    system->set_control_box_serial_number("CX01-01-T1-000001");
    system->mutable_manipulator()->set_name("arm");
    system->mutable_manipulator()->set_arm_serial_number("A02L-00-M3-000001");

    grpc::ClientContext context;
    flexiv::pdk::SaveConfigResponse response;
    client.config().stub->Save(&context, request, &response);
  }

  std::cout << "Saving collision configuration..." << std::endl;
  const std::string collision_config_name = "default_collision_config";
  {
    flexiv::pdk::scene::collision::SaveRequest request;
    request.mutable_collision_config()->set_name(collision_config_name);
    request.mutable_collision_config()->set_collision_margin(0.0);

    grpc::ClientContext context;
    flexiv::pdk::scene::collision::SaveResponse response;
    const grpc::Status status = client.collision().stub->Save(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Save collision config failed: " << status.error_message() << std::endl;
    }
  }

  // The pose FK returns for the joint positions below; used if FK fails.
  SE3Pose fk_pose;
  fk_pose.mutable_position()->set_x(0.13599999999999995);
  fk_pose.mutable_position()->set_y(-0.11000000000000004);
  fk_pose.mutable_position()->set_z(1.2550000000000001);
  fk_pose.mutable_rotation()->set_x(8.65956056235493e-17);
  fk_pose.mutable_rotation()->set_y(0.70710678118654746);
  fk_pose.mutable_rotation()->set_z(-1.7319121124709863e-16);
  fk_pose.mutable_rotation()->set_w(0.70710678118654757);

  const std::vector<double> joint_positions = {1.0, 0.4, 0.3, 1.5708, 0.5, 0.4, 0.0};

  std::cout << "Computing Forward Kinematics for system_1.arm.flange..." << std::endl;
  {
    FKRequest request;
    request.set_system_name("system_1");
    request.set_target_frame_name("system_1.arm.flange");
    for (double joint : joint_positions) {
      request.add_joint_positions(joint);
    }

    grpc::ClientContext context;
    FKResponse response;
    const auto start = std::chrono::steady_clock::now();
    const grpc::Status status = client.kinematics().stub->ComputeFK(&context, request, &response);
    const double elapsed_ms = MillisecondsSince(start);
    if (!status.ok()) {
      std::cerr << "Kinematics error: " << status.error_message() << std::endl;
    } else {
      fk_pose = response.pose();
      std::cout << std::endl
                << "--- Forward Kinematics Result (" << std::fixed << std::setprecision(2)
                << elapsed_ms << " ms) ---" << std::endl
                << std::defaultfloat << response.DebugString()
                << "---------------------------------" << std::endl;
    }
  }

  std::cout << "Computing Inverse Kinematics for system_1.arm.flange without seed..." << std::endl;
  ComputeIK(client, fk_pose, collision_config_name, {});

  std::this_thread::sleep_for(std::chrono::milliseconds(100));
  std::cout << "Computing Inverse Kinematics for system_1.arm.flange with seed..." << std::endl;
  ComputeIK(client, fk_pose, collision_config_name, joint_positions);

  return 0;
}
