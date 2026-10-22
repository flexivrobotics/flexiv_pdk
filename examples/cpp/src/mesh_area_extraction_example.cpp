/**
 * @file mesh_area_extraction_example.cpp
 * @brief Example: Extract an area from a mesh object.
 *
 * This program demonstrates how to:
 *   1. Create a new workcell
 *   2. Add a plane mesh object to the scene
 *   3. Extract an area from a mesh using the mesh operation service
 *
 * Needs a mesh_operation license. Copy the plane mesh file "plane_1m_10x10.obj" in the assets
 * directory to "flexiv_pdk_data/user_data/meshes/" on the server machine. That folder is beside
 * your flexiv_pdk folder.
 */

#include <flexiv/pdk/client.hpp>
#include <flexiv/pdk/config_header.pb.h>
#include <flexiv/pdk/config_service.pb.h>
#include <flexiv/pdk/mesh_operation/service.pb.h>
#include <flexiv/pdk/scene/object.pb.h>
#include <flexiv/pdk/workcell/workcell_service.pb.h>

#include <array>
#include <cstdlib>
#include <iostream>
#include <string>

using flexiv::pdk::Client;
using flexiv::pdk::ConfigHeader;
using flexiv::pdk::common::Status;
using flexiv::pdk::scene::Object;

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

// An object whose visual and collision shapes are both the mesh at mesh_path.
Object MakeMeshObject(const std::string& name, double px, double py, double pz,
    const std::string& mesh_path, double scale = 1.0)
{
  Object object;
  *object.mutable_header() = MakeHeader(name, "world", px, py, pz);

  auto* visual = object.add_visual();
  visual->mutable_origin()->mutable_rotation()->set_w(1.0);
  auto* mesh = visual->mutable_shape()->mutable_mesh();
  mesh->set_filename(mesh_path);
  mesh->mutable_scale()->set_x(scale);
  mesh->mutable_scale()->set_y(scale);
  mesh->mutable_scale()->set_z(scale);

  auto* collision = object.add_collision();
  *collision->mutable_origin() = visual->origin();
  *collision->mutable_shape() = visual->shape();
  return object;
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
    create_request.set_description("Example workcell for mesh area extraction");
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
  {
    flexiv::pdk::SaveConfigRequest request;
    *request.mutable_object() = MakeMeshObject("mesh_1", 0.0, 0.0, 0.0, kMeshPath);
    grpc::ClientContext context;
    flexiv::pdk::SaveConfigResponse response;
    client.config().stub->Save(&context, request, &response);
  }

  // 3. Extract area from mesh_1 using the MeshOperation service, and save the resulting area as a
  // new object in the scene
  std::cout << "Extracting area from mesh and saving as new object..." << std::endl;
  {
    flexiv::pdk::AreaExtractionRequest request;
    request.set_object_name("mesh_1");
    request.set_extracted_object_name("extracted_area_1");
    constexpr std::array<std::array<double, 2>, 4> kBoundary
        = {{{0.2, 0.2}, {0.4, 0.2}, {0.4, 0.4}, {0.2, 0.4}}};
    for (const auto& [x, y] : kBoundary) {
      auto* point = request.add_boundary();
      point->set_x(x);
      point->set_y(y);
      point->set_z(0.0);
    }

    grpc::ClientContext context;
    flexiv::pdk::AreaExtractionResponse response;
    const grpc::Status status
        = client.mesh_operation().stub->ExtractArea(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Area extraction failed: " << status.error_message() << std::endl;
    } else if (response.status().code() == Status::OK) {
      std::cout << "Area extraction successful, saving extracted area to the scene..." << std::endl;
    } else {
      std::cout << "Area extraction failed: " << response.status().message() << std::endl;
      return 1;
    }
  }

  return 0;
}
