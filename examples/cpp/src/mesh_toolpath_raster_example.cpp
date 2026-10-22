/**
 * @file mesh_toolpath_raster_example.cpp
 * @brief Example: Create a raster toolpath from a plane mesh.
 *
 * This program demonstrates how to:
 *   1. Create a new workcell
 *   2. Add a plane mesh object to the scene
 *   3. Generate a raster path for a mesh using the surface finish service
 *
 * Needs a surface_finish license. Copy the plane mesh file "plane_1m_10x10.obj" in the assets
 * directory to "flexiv_pdk_data/user_data/meshes/" on the server machine. That folder is beside
 * your flexiv_pdk folder.
 */

#include <flexiv/pdk/client.hpp>
#include <flexiv/pdk/config_header.pb.h>
#include <flexiv/pdk/config_service.pb.h>
#include <flexiv/pdk/scene/object.pb.h>
#include <flexiv/pdk/surface_finish/generator/mesh_raster_path.pb.h>
#include <flexiv/pdk/surface_finish/service.pb.h>
#include <flexiv/pdk/workcell/workcell_service.pb.h>

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
    create_request.set_description("Example workcell for mesh toolpath raster generation");
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
  std::cout << "Saving objects to the scene..." << std::endl;
  {
    flexiv::pdk::SaveConfigRequest request;
    *request.mutable_object() = MakeMeshObject("mesh_1", 0.0, 0.0, 0.0, kMeshPath);
    grpc::ClientContext context;
    flexiv::pdk::SaveConfigResponse response;
    client.config().stub->Save(&context, request, &response);
  }

  // 3. Run the surface finish service to generate a raster path on the mesh
  std::cout << "Generating raster path for the mesh..." << std::endl;
  {
    flexiv::pdk::surface_finish::generator::GenerateNominalPathRequest request;
    request.mutable_header()->set_name("path");
    request.mutable_header()->set_parent("mesh_1");
    auto* raster = request.mutable_mesh_raster_path();
    raster->set_fixed_spacing(0.02);
    raster->set_blending_radius(0.0);
    raster->set_border_offset(0.0);
    raster->set_raster_line_spacing(0.04);
    raster->set_raster_path_joining_distance_threshold(0.08);
    raster->set_principal_rotation_angle(0.0);
    raster->set_align_with_initial_direction(true);

    grpc::ClientContext context;
    flexiv::pdk::surface_finish::generator::GenerateNominalPathResponse response;
    const grpc::Status status
        = client.surface_finish().stub->GenerateNominalPath(&context, request, &response);
    if (!status.ok()) {
      std::cerr << "Surface finish service call failed: " << status.error_message() << std::endl;
    } else if (response.status().code() == Status::OK && response.path_names_size() > 0) {
      std::cout << "Successfully generated raster path for the mesh." << std::endl;
    } else {
      std::cout << "Surface finish service call failed: " << response.status().message()
                << std::endl;
      return 1;
    }
  }

  return 0;
}
