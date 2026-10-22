/**
 * @file scene_example.cpp
 * @brief Example: Create a simple scene using the Flexiv PDK.
 *
 * This program demonstrates how to:
 *   1. Create a new workcell
 *   2. Add multiple objects to the scene
 *   3. Add two robot systems to the scene, separated by 1.4 meters and facing each other
 */

#include <flexiv/pdk/client.hpp>
#include <flexiv/pdk/config_header.pb.h>
#include <flexiv/pdk/config_service.pb.h>
#include <flexiv/pdk/scene/object.pb.h>
#include <flexiv/pdk/system/components/manipulator.pb.h>
#include <flexiv/pdk/system/system.pb.h>
#include <flexiv/pdk/workcell/workcell_service.pb.h>

#include <cstdlib>
#include <iostream>
#include <string>

using flexiv::pdk::Client;
using flexiv::pdk::ConfigHeader;

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

void SaveObject(Client& client, const ConfigHeader& header)
{
  // Required fields for Object: header (name, parent, pose_in_parent)
  // Optional Object fields: inertial, collision, reference_only, visual
  flexiv::pdk::SaveConfigRequest request;
  *request.mutable_object()->mutable_header() = header;
  grpc::ClientContext context;
  flexiv::pdk::SaveConfigResponse response;
  client.config().stub->Save(&context, request, &response);
}

void SaveSystem(Client& client, const ConfigHeader& header,
    const std::string& control_box_serial_number, const std::string& arm_serial_number)
{
  flexiv::pdk::SaveConfigRequest request;
  auto* system = request.mutable_system();
  *system->mutable_header() = header;
  system->set_control_box_serial_number(control_box_serial_number);
  system->mutable_manipulator()->set_name("arm");
  system->mutable_manipulator()->set_arm_serial_number(arm_serial_number);
  grpc::ClientContext context;
  flexiv::pdk::SaveConfigResponse response;
  client.config().stub->Save(&context, request, &response);
}

} // namespace

int main()
{
  const std::string target = ServerAddress();
  std::cout << "Connecting to the PDK server at " << target << "..." << std::endl;

  Client client(target);

  // 1. Create a workcell
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

  // 2. Add objects to the scene
  std::cout << "Saving objects to the scene..." << std::endl;
  SaveObject(client, MakeHeader("box_1", "world", 0.5, 0.0, 0.0));
  SaveObject(client, MakeHeader("box_2", "world", 0.5, 0.5, 0.0));
  SaveObject(client, MakeHeader("box_3", "world", 0.5, 1.0, 0.0));

  // 3. Add two robot systems to the scene
  std::cout << "Saving robot systems to the scene..." << std::endl;

  // System 1: Placed at x=-0.7, facing +x (rz=0)
  SaveSystem(client, MakeHeader("system_1", "world", -0.7, 0.0, 0.0), "CX01-01-T1-000001",
      "A02L-00-M3-000001");

  // System 2: Placed at x=0.7, facing -x (rz=1, rw=0 -> 180 degrees around Z)
  SaveSystem(client, MakeHeader("system_2", "world", 0.7, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
      "CX01-01-T1-000002", "A02L-00-M3-000002");

  std::cout << "Commands executed to create workcell, 3 objects, and 2 systems in the scene!"
            << std::endl;

  return 0;
}
