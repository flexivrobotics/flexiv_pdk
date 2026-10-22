#include "flexiv/pdk/client.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <stdexcept>
#include <utility>

#include "flexiv/pdk/common/version.h"

namespace flexiv {
namespace pdk {

namespace {

constexpr char kBase64Alphabet[]
    = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

bool IsBase64Character(char c)
{
  return std::isalnum(static_cast<unsigned char>(c)) != 0 || c == '+' || c == '/' || c == '=';
}

std::string Base64Encode(const std::string& bytes)
{
  std::string encoded;
  encoded.reserve((bytes.size() + 2) / 3 * 4);
  for (std::size_t i = 0; i < bytes.size(); i += 3) {
    const std::size_t n = std::min<std::size_t>(3, bytes.size() - i);
    std::uint32_t chunk = 0;
    for (std::size_t j = 0; j < n; ++j) {
      chunk |= static_cast<std::uint32_t>(static_cast<unsigned char>(bytes[i + j])) << (16 - 8 * j);
    }
    for (std::size_t j = 0; j < 4; ++j) {
      encoded += j <= n ? kBase64Alphabet[(chunk >> (18 - 6 * j)) & 0x3F] : '=';
    }
  }
  return encoded;
}

// The base64 that SaveRequest.license expects, from either form of license file. A raw bundle is
// protobuf, so it carries bytes outside the base64 alphabet; that is what tells the forms apart.
std::string LicenseText(const std::string& raw)
{
  std::string compact;
  std::copy_if(raw.begin(), raw.end(), std::back_inserter(compact),
      [](char c) { return c != ' ' && c != '\t' && c != '\r' && c != '\n'; });
  if (!compact.empty() && std::all_of(compact.begin(), compact.end(), IsBase64Character)) {
    return compact;
  }
  return Base64Encode(raw);
}

// The file's own name if the server accepts it as a plain name, otherwise "" so the server names
// the file after the license id.
std::string ServerFileName(const std::string& path)
{
  const std::string name = path.substr(path.find_last_of('/') + 1);
  const bool plain = !name.empty() && std::all_of(name.begin(), name.end(), [](char c) {
    return std::isalnum(static_cast<unsigned char>(c)) != 0 || c == '-' || c == '_' || c == '.';
  });
  return plain ? name : "";
}

} // namespace

grpc::Status LicenseServiceClient::InstallFile(
    const std::string& path, license::SaveResponse* response, const std::string& file_name)
{
  std::ifstream file(path, std::ios::binary);
  if (!file) {
    throw std::runtime_error("Cannot read " + path);
  }
  const std::string raw((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
  if (std::all_of(raw.begin(), raw.end(),
          [](char c) { return std::isspace(static_cast<unsigned char>(c)) != 0; })) {
    throw std::runtime_error(path + " is empty. Ask Flexiv to send it again.");
  }

  license::SaveRequest request;
  request.set_license(LicenseText(raw));
  request.set_file_name(file_name.empty() ? ServerFileName(path) : file_name);
  grpc::ClientContext context;
  return stub->Save(&context, request, response);
}

Client::Client(const std::string& target)
: channel_(grpc::CreateChannel(target, grpc::InsecureChannelCredentials()))
{
  std::fprintf(stderr, "[flexiv::pdk::Client] SDK version [%s] hash [%s] connecting to [%s]\n",
      FLEXIV_PDK_VERSION.c_str(), FLEXIV_PDK_VERSION_HASH.c_str(), target.c_str());
}

Client::Client(std::shared_ptr<grpc::Channel> channel)
: channel_(std::move(channel))
{
  if (!channel_) {
    throw std::invalid_argument("Client channel cannot be null");
  }
}

template <typename ServiceClientT>
ServiceClientT& Client::LazyInit(std::unique_ptr<ServiceClientT>& service_client)
{
  std::lock_guard<std::mutex> lock(mutex_);
  if (!channel_) {
    throw std::runtime_error("PDK client channel is closed");
  }
  if (!service_client) {
    service_client = std::make_unique<ServiceClientT>(channel_);
  }
  return *service_client;
}

VersionServiceClient& Client::version()
{
  return LazyInit(version_);
}

LogServiceClient& Client::log()
{
  return LazyInit(log_);
}

FrameServiceClient& Client::frame()
{
  return LazyInit(frame_);
}

SceneEventServiceClient& Client::scene_event()
{
  return LazyInit(scene_event_);
}

WorkcellServiceClient& Client::workcell()
{
  return LazyInit(workcell_);
}

CollisionServiceClient& Client::collision()
{
  return LazyInit(collision_);
}

ComponentsServiceClient& Client::system_config()
{
  return LazyInit(system_config_);
}

StateServiceClient& Client::system_state()
{
  return LazyInit(system_state_);
}

SystemServiceClient& Client::system()
{
  return LazyInit(system_);
}

KinematicsServiceClient& Client::kinematics()
{
  return LazyInit(kinematics_);
}

SurfaceFinishServiceClient& Client::surface_finish()
{
  return LazyInit(surface_finish_);
}

ConfigServiceClient& Client::config()
{
  return LazyInit(config_);
}

PointToPointPathServiceClient& Client::point_to_point_path()
{
  return LazyInit(point_to_point_path_);
}

LicenseServiceClient& Client::license()
{
  return LazyInit(license_);
}

MeshOperationServiceClient& Client::mesh_operation()
{
  return LazyInit(mesh_operation_);
}

CameraServiceClient& Client::camera()
{
  return LazyInit(camera_);
}

ReconstructionServiceClient& Client::reconstruction()
{
  return LazyInit(reconstruction_);
}

bool Client::CheckVersion(std::string* message)
{
  common::GetVersionRequest request;
  request.mutable_client_version()->set_major(FLEXIV_PDK_VERSION_MAJOR);
  request.mutable_client_version()->set_minor(FLEXIV_PDK_VERSION_MINOR);
  request.mutable_client_version()->set_patch(FLEXIV_PDK_VERSION_PATCH);

  common::GetVersionResponse response;
  grpc::ClientContext context;
  const grpc::Status status = version().stub->GetVersion(&context, request, &response);
  if (!status.ok()) {
    if (message) {
      *message = "Cannot get the server version: " + status.error_message();
    }
    return false;
  }

  const common::Version& server = response.server_version();
  const std::string server_version = std::to_string(server.major()) + "."
                                     + std::to_string(server.minor()) + "."
                                     + std::to_string(server.patch());
  if (message) {
    *message = response.compatible()
                   ? "Server version " + server_version
                   : "Client " + FLEXIV_PDK_VERSION + " does not work with server " + server_version
                         + ". Use a client and server with the same major and minor version.";
  }
  return response.compatible();
}

std::shared_ptr<grpc::Channel> Client::channel() const
{
  std::lock_guard<std::mutex> lock(mutex_);
  return channel_;
}

void Client::close()
{
  std::lock_guard<std::mutex> lock(mutex_);

  version_.reset();
  log_.reset();
  frame_.reset();
  scene_event_.reset();
  workcell_.reset();
  collision_.reset();
  system_config_.reset();
  system_state_.reset();
  system_.reset();
  kinematics_.reset();
  surface_finish_.reset();
  config_.reset();
  point_to_point_path_.reset();
  license_.reset();
  mesh_operation_.reset();
  camera_.reset();
  reconstruction_.reset();

  channel_.reset();
}

} // namespace pdk
} // namespace flexiv
