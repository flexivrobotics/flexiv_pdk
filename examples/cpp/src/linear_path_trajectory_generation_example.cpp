/**
 * @file linear_path_trajectory_generation_example.cpp
 * @brief Example: Create a toolpath sketch from a plane mesh and generate a RCA trajectory for a
 * robot to follow the path.
 *
 * This program demonstrates how to:
 *   1. Create a new workcell
 *   2. Add a plane mesh object to the scene
 *   3. Add a robot system to the scene
 *   4. Generate a sketch path for a mesh using the surface finish service
 *   5. Solve for the robot motion along the generated path
 *   6. Set Cartesian velocity, acceleration, and force for the robot motion
 *   7. Generate the RCA trajectory for the robot motion
 *
 * Needs a surface_finish license. Copy the plane mesh file "plane_1m_10x10.obj" in the assets
 * directory to "flexiv_pdk_data/user_data/meshes/" on the server machine. That folder is beside
 * your flexiv_pdk folder.
 */

#include <flexiv/pdk/client.hpp>
#include <flexiv/pdk/config_header.pb.h>
#include <flexiv/pdk/config_service.pb.h>
#include <flexiv/pdk/scene/object.pb.h>
#include <flexiv/pdk/surface_finish/generator/mesh_sketch_path.pb.h>
#include <flexiv/pdk/surface_finish/path.pb.h>
#include <flexiv/pdk/surface_finish/service.pb.h>
#include <flexiv/pdk/surface_finish/solver_preferences.pb.h>
#include <flexiv/pdk/system/components/manipulator.pb.h>
#include <flexiv/pdk/system/system.pb.h>
#include <flexiv/pdk/workcell/workcell_service.pb.h>

#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

using flexiv::pdk::Client;
using flexiv::pdk::ConfigHeader;
using flexiv::pdk::common::Status;
using flexiv::pdk::spatial::CartesianWaypoint;
using flexiv::pdk::surface_finish::SolverPreferences;

namespace generator = flexiv::pdk::surface_finish::generator;

namespace {

const std::string kMeshPath = "/home/flexiv/user_data/meshes/plane_1m_10x10.obj";

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

// Sets the speed, acceleration and pressing force the robot uses along a waypoint.
void SetMotion(CartesianWaypoint* waypoint)
{
  waypoint->set_velocity(0.1);
  waypoint->set_acceleration(0.2);
  waypoint->mutable_wrench()->mutable_force()->set_z(5);
}

} // namespace

int main()
{
  const std::string target = ServerAddress();
  std::cout << "Connecting to the PDK server at " << target << "..." << std::endl;

  Client client(target);

  // 1. Create a workcell
  const std::string workcell_name = "example_workcell";

  // Remove any existing workcell
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
    create_request.set_description("Example workcell for linear path trajectory generation");
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

  // 2. Add plane mesh object to the scene
  std::cout << "Adding plane mesh object to the scene..." << std::endl;
  {
    flexiv::pdk::SaveConfigRequest request;
    auto* object = request.mutable_object();
    *object->mutable_header() = MakeHeader("mesh_1", "world", 0.8, 0.0, 0.0);
    auto* visual = object->add_visual();
    visual->mutable_origin()->mutable_rotation()->set_w(1.0);
    auto* mesh = visual->mutable_shape()->mutable_mesh();
    mesh->set_filename(kMeshPath);
    mesh->mutable_scale()->set_x(1.0);
    mesh->mutable_scale()->set_y(1.0);
    mesh->mutable_scale()->set_z(1.0);

    grpc::ClientContext context;
    flexiv::pdk::SaveConfigResponse response;
    client.config().stub->Save(&context, request, &response);
  }

  // 3. Add a robot system to the scene
  std::cout << "Saving robot system to the scene..." << std::endl;
  {
    flexiv::pdk::SaveConfigRequest request;
    auto* system = request.mutable_system();
    *system->mutable_header() = MakeHeader("system_1", "world", 0.05, 0.0, 0.0);
    system->set_control_box_serial_number("CX01-01-T1-000001");
    system->mutable_manipulator()->set_name("arm");
    system->mutable_manipulator()->set_arm_serial_number("A02L-00-M3-000001");

    grpc::ClientContext context;
    flexiv::pdk::SaveConfigResponse response;
    client.config().stub->Save(&context, request, &response);
  }

  // 4. Run the surface finish service to generate a sketch path for the mesh. The specified points
  // are in the mesh's local frame, and the generated path will be saved as a new config in the
  // scene.
  std::cout << "Generating sketch path for the mesh..." << std::endl;
  std::vector<std::string> path_names;
  {
    generator::GenerateNominalPathRequest request;
    request.mutable_header()->set_name("path_long_sketch");
    request.mutable_header()->set_parent("mesh_1");
    auto* sketch = request.mutable_mesh_sketch_path();
    sketch->add_points()->set_x(-0.05);
    sketch->add_points()->set_x(-0.45);
    sketch->set_blending_radius(0.0);
    sketch->set_fixed_spacing(0.01);
    sketch->set_align_with_initial_direction(true);

    grpc::ClientContext context;
    generator::GenerateNominalPathResponse response;
    const grpc::Status status
        = client.surface_finish().stub->GenerateNominalPath(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Surface finish service call failed: " << status.error_message() << std::endl;
      return 1;
    }
    if (response.status().code() != Status::OK) {
      std::cout << "Surface finish service call failed: " << response.status().message()
                << std::endl;
      return 1;
    }
    std::cout << "Successfully generated sketch path for the mesh." << std::endl;
    path_names.assign(response.path_names().begin(), response.path_names().end());
  }

  // 5. Run Basic solve to compute the robot joint positions for the generated path
  std::cout << "Running basic solve for the generated long path..." << std::endl;
  for (const auto& path_name : path_names) {
    generator::CreateRobotMotionRequest request;
    request.set_path_name(path_name);
    auto* preferences = request.mutable_solver_preferences();
    preferences->set_system_name("system_1");
    preferences->set_tcp_ecp_name("system_1.arm.flange");
    preferences->set_solver_type(SolverPreferences::SOLVER_TYPE_BASIC);

    grpc::ClientContext context;
    generator::CreateRobotMotionResponse response;
    const grpc::Status status
        = client.surface_finish().stub->CreateRobotMotion(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Failed to solve path config: " << status.error_message() << std::endl;
      return 1;
    }
    if (response.status().code() == Status::OK) {
      std::cout << "Successfully created robot motion for path " << path_name << "." << std::endl;
    } else {
      std::cout << "Failed to create robot motion for path " << path_name << ": "
                << response.status().message() << std::endl;
    }
  }

  // 6. Get the generated path config and set the Cartesian velocity and acceleration for the robot
  // motion
  std::cout << "Setting Cartesian velocity, acceleration, and force for the generated path..."
            << std::endl;
  for (const auto& path_name : path_names) {
    generator::GetRequest get_request;
    get_request.set_path_name(path_name);

    grpc::ClientContext get_context;
    generator::GetResponse get_response;
    grpc::Status status
        = client.surface_finish().stub->Get(&get_context, get_request, &get_response);
    if (!status.ok()) {
      std::cerr << "Failed to get path config: " << status.error_message() << std::endl;
      return 1;
    }
    if (get_response.status().code() != Status::OK) {
      std::cout << "Failed to get path config for " << path_name << ": "
                << get_response.status().message() << std::endl;
      continue;
    }

    flexiv::pdk::SaveConfigRequest save_request;
    auto* path = save_request.mutable_surface_path();
    *path = get_response.path();
    for (auto& waypoint : *path->mutable_nominal_cartesian()) {
      SetMotion(&waypoint);
    }
    for (auto& waypoint : *path->mutable_refined_cartesian()) {
      SetMotion(&waypoint);
    }

    grpc::ClientContext save_context;
    flexiv::pdk::SaveConfigResponse save_response;
    status = client.config().stub->Save(&save_context, save_request, &save_response);
    if (!status.ok()) {
      std::cerr << "Failed to save path config: " << status.error_message() << std::endl;
      return 1;
    }
    std::cout << "Successfully set Cartesian velocity, acceleration, and force for path "
              << path_name << "." << std::endl;
  }

  // 7. Generate the RCA trajectory for the robot motion. The generated trajectory .traj file will
  // be saved in the PDK server as {workcell}/linear_path/{path_name}/{path_name}.traj.
  std::cout << "Generating RCA trajectory for the robot motion..." << std::endl;
  for (const auto& path_name : path_names) {
    generator::GenerateRCATrajectoryFileRequest request;
    request.set_path_name(path_name);

    grpc::ClientContext context;
    generator::GenerateRCATrajectoryFileResponse response;
    const grpc::Status status
        = client.surface_finish().stub->GenerateRCATrajectoryFile(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Failed to generate RCA trajectory: " << status.error_message() << std::endl;
      return 1;
    }
    if (response.status().code() == Status::OK) {
      std::cout << "Successfully created RCA trajectory for path " << path_name << "." << std::endl;
    } else {
      std::cout << "Failed to create RCA trajectory for path " << path_name << ": "
                << response.status().message() << std::endl;
    }
  }

  return 0;
}
