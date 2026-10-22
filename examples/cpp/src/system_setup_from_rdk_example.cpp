/**
 * @file system_setup_from_rdk_example.cpp
 * @brief Example: Create a system setup in the PDK server by connecting to an RDK and saving its
 * configuration to the PDK server.
 *
 * This program demonstrates how to:
 *   1. Remove existing workcell and create a new one
 *   2. Add a robot system to the scene by connecting to an RDK and saving its configuration to the
 *      PDK server
 *   3. List existing systems in the scene
 *
 * Note: Remember to modify the `serial_number` variable to match your RDK's serial number before
 * running the program.
 */

#include <flexiv/pdk/client.hpp>
#include <flexiv/pdk/config_service.pb.h>
#include <flexiv/pdk/system/system_service.pb.h>
#include <flexiv/pdk/workcell/workcell_service.pb.h>

#include <cstdlib>
#include <iostream>
#include <string>

using flexiv::pdk::Client;
using flexiv::pdk::common::Status;

namespace {

std::string ServerAddress()
{
  const char* address = std::getenv("PDK_SERVER_ADDR");
  return address != nullptr ? address : "localhost:50052";
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
  std::cout << "Add a system by connecting to the RDK and saving its configuration to the PDK "
               "server"
            << std::endl;
  const std::string system_name = "system_1";
  const std::string serial_number = "Rizon4-062065";
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

  // 4. List existing systems in the scene
  {
    flexiv::pdk::ListConfigRequest request;
    request.set_type(flexiv::pdk::CONFIG_TYPE_SYSTEM);

    grpc::ClientContext context;
    flexiv::pdk::ListConfigResponse response;
    const grpc::Status status = client.config().stub->List(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Failed to list systems: " << status.error_message() << std::endl;
    } else {
      std::cout << "Existing systems in the scene:" << std::endl;
      for (const auto& name : response.names()) {
        std::cout << "- " << name << std::endl;
      }
    }
  }

  return 0;
}
