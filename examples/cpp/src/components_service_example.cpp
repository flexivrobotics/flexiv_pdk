/**
 * @file components_service_example.cpp
 * @brief Example: Create a workcell, add a robot system, and query the components service using the
 * Flexiv PDK.
 *
 * This program demonstrates how to:
 *   1. Create a new workcell
 *   2. Add one robot system to the scene
 *   3. Query the components service for information about the robot system and available
 *      components
 *   4. Create a custom tool using the components service
 */

#include <flexiv/pdk/client.hpp>
#include <flexiv/pdk/config_header.pb.h>
#include <flexiv/pdk/config_service.pb.h>
#include <flexiv/pdk/system/components/custom_tool.pb.h>
#include <flexiv/pdk/system/components/custom_tool_adapter.pb.h>
#include <flexiv/pdk/system/components/manipulator.pb.h>
#include <flexiv/pdk/system/components/tool.pb.h>
#include <flexiv/pdk/system/components_service.pb.h>
#include <flexiv/pdk/system/system.pb.h>
#include <flexiv/pdk/system/system_service.pb.h>
#include <flexiv/pdk/workcell/workcell_service.pb.h>
#include <google/protobuf/empty.pb.h>

#include <cstdlib>
#include <iostream>
#include <string>

using flexiv::pdk::Client;
using flexiv::pdk::ConfigHeader;
using flexiv::pdk::common::Status;
using flexiv::pdk::spatial::SE3Pose;
using flexiv::pdk::system::ListManufacturerModelResponse;

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

SE3Pose MakePose(double px, double py, double pz)
{
  SE3Pose pose;
  pose.mutable_position()->set_x(px);
  pose.mutable_position()->set_y(py);
  pose.mutable_position()->set_z(pz);
  pose.mutable_rotation()->set_w(1.0);
  return pose;
}

// Prints every manufacturer and model returned by one of the components service List RPCs.
void PrintManufacturerModels(const std::string& rpc_name, const std::string& label,
    const grpc::Status& status, const ListManufacturerModelResponse& response)
{
  if (!status.ok()) {
    std::cerr << rpc_name << " failed: " << status.error_message() << std::endl;
    return;
  }
  if (response.status().code() == Status::OK) {
    for (const auto& item : response.items()) {
      std::cout << label << " manufacturer: " << item.manufacturer() << ", model: " << item.model()
                << std::endl;
    }
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

  // 3. Create a custom tool
  std::cout << std::endl << "Creating custom tool..." << std::endl;
  {
    flexiv::pdk::system::SaveCustomToolRequest request;
    auto* custom_tool = request.mutable_custom_tool();
    custom_tool->set_manufacturer("example_manufacturer");
    custom_tool->set_model("example_model");
    *custom_tool->mutable_tcp() = MakePose(0.0, 0.0, 0.1);

    auto* collision = custom_tool->add_collision();
    *collision->mutable_origin() = MakePose(0.0, 0.0, 0.05);
    auto* collision_box = collision->mutable_shape()->mutable_box();
    collision_box->add_size(0.05);
    collision_box->add_size(0.05);
    collision_box->add_size(0.05);

    auto* visual = custom_tool->add_visual();
    *visual->mutable_origin() = *collision->mutable_origin();
    *visual->mutable_shape() = collision->shape();

    grpc::ClientContext context;
    flexiv::pdk::system::SaveCustomToolResponse response;
    const grpc::Status status
        = client.system_config().stub->SaveCustomTool(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "SaveCustomTool failed: " << status.error_message() << std::endl;
    } else if (response.status().code() == Status::OK) {
      std::cout << "Custom tool saved successfully." << std::endl;
    } else {
      std::cout << "SaveCustomTool returned status: " << response.status().ShortDebugString()
                << std::endl;
    }
  }

  // 4. Create a custom tool adapter
  std::cout << std::endl << "Creating custom tool adapter..." << std::endl;
  {
    flexiv::pdk::system::SaveCustomToolAdapterRequest request;
    auto* custom_tool_adapter = request.mutable_custom_tool_adapter();
    custom_tool_adapter->set_manufacturer("example_manufacturer");
    custom_tool_adapter->set_model("example_model");
    *custom_tool_adapter->add_flange() = MakePose(0.0, 0.0, 0.0);

    grpc::ClientContext context;
    flexiv::pdk::system::SaveCustomToolAdapterResponse response;
    const grpc::Status status
        = client.system_config().stub->SaveCustomToolAdapter(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "SaveCustomToolAdapter failed: " << status.error_message() << std::endl;
    } else if (response.status().code() == Status::OK) {
      std::cout << "Custom tool adapter saved successfully." << std::endl;
    } else {
      std::cout << "SaveCustomToolAdapter returned status: " << response.status().ShortDebugString()
                << std::endl;
    }
  }

  const google::protobuf::Empty empty;

  // 5. List the available tool adapters
  std::cout << std::endl << "Listing tool adapters..." << std::endl;
  {
    grpc::ClientContext context;
    ListManufacturerModelResponse response;
    const grpc::Status status
        = client.system_config().stub->ListToolAdapters(&context, empty, &response);
    PrintManufacturerModels("ListToolAdapters", "Tool adapter", status, response);
  }

  // 6. List the available tools
  std::cout << std::endl << "Listing tools..." << std::endl;
  {
    grpc::ClientContext context;
    ListManufacturerModelResponse response;
    const grpc::Status status = client.system_config().stub->ListTools(&context, empty, &response);
    PrintManufacturerModels("ListTools", "Tool", status, response);
  }

  // 7. List the available custom tools
  std::cout << std::endl << "Listing custom tools..." << std::endl;
  {
    grpc::ClientContext context;
    ListManufacturerModelResponse response;
    const grpc::Status status
        = client.system_config().stub->ListCustomTools(&context, empty, &response);
    PrintManufacturerModels("ListCustomTools", "Custom tool", status, response);
  }

  // 8. List the available custom tool adapters
  std::cout << std::endl << "Listing custom tool adapters..." << std::endl;
  {
    grpc::ClientContext context;
    ListManufacturerModelResponse response;
    const grpc::Status status
        = client.system_config().stub->ListCustomToolAdapters(&context, empty, &response);
    PrintManufacturerModels("ListCustomToolAdapters", "Custom tool adapter", status, response);
  }

  // 9. List the available external robot axes
  std::cout << std::endl << "Listing external robot axes..." << std::endl;
  {
    grpc::ClientContext context;
    ListManufacturerModelResponse response;
    const grpc::Status status
        = client.system_config().stub->ListExternalRobotAxes(&context, empty, &response);
    PrintManufacturerModels("ListExternalRobotAxes", "External robot axis", status, response);
  }

  // 10. Add a robot system to the scene with the custom tool from step 3
  const std::string system_name = "system_2";
  std::cout << std::endl << "Saving robot system with custom tool to the scene..." << std::endl;
  {
    flexiv::pdk::SaveConfigRequest request;
    auto* system = request.mutable_system();
    *system->mutable_header() = MakeHeader(system_name, "world", 1.0, 0.0, 0.0);
    system->set_control_box_serial_number("CX01-01-T1-000002");
    system->mutable_manipulator()->set_name("arm");
    system->mutable_manipulator()->set_arm_serial_number("A02L-00-M3-000002");
    auto* tool = system->add_tool();
    tool->set_name("example_tool");
    tool->set_manufacturer("example_manufacturer");
    tool->set_model("example_model");

    grpc::ClientContext context;
    flexiv::pdk::SaveConfigResponse response;
    client.config().stub->Save(&context, request, &response);
  }

  // 11. Get the system urdf
  std::cout << "Getting system urdf..." << std::endl;
  {
    grpc::ClientContext context;
    flexiv::pdk::system::GetUrdfRequest request;
    flexiv::pdk::system::GetUrdfResponse response;
    request.set_name(system_name);
    const grpc::Status status = client.system().stub->GetUrdf(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "GetURDF failed: " << status.error_message() << std::endl;
    } else if (response.status().code() == Status::OK) {
      std::cout << "URDF for " << system_name << ":" << std::endl
                << response.urdf_content() << std::endl;
    }
  }

  // 12. Get the arm serial number
  std::cout << std::endl << "Getting arm serial number..." << std::endl;
  {
    grpc::ClientContext context;
    flexiv::pdk::system::GetArmSerialNumberRequest request;
    flexiv::pdk::system::GetArmSerialNumberResponse response;
    request.set_system_name(system_name);
    const grpc::Status status
        = client.system().stub->GetArmSerialNumber(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "GetArmSerialNumber failed: " << status.error_message() << std::endl;
    } else if (response.status().code() == Status::OK) {
      std::cout << "Arm serial number for " << system_name << ": " << response.arm_serial_number()
                << std::endl;
      std::cout << "Arm public serial number for " << system_name << ": "
                << response.arm_public_serial_number() << std::endl;
    }
  }

  return 0;
}
