#ifndef FLEXIV_PDK_CLIENT_HPP_
#define FLEXIV_PDK_CLIENT_HPP_

// GRPC related headers
#include <grpc/grpc.h>
#include <grpcpp/channel.h>
#include <grpcpp/client_context.h>
#include <grpcpp/create_channel.h>

#include <memory>
#include <mutex>
#include <string>

#include "flexiv/pdk/camera/service.grpc.pb.h"
#include "flexiv/pdk/common/log_service.grpc.pb.h"
#include "flexiv/pdk/common/version_service.grpc.pb.h"
#include "flexiv/pdk/config_service.grpc.pb.h"
#include "flexiv/pdk/frame_service.grpc.pb.h"
#include "flexiv/pdk/license/license_service.grpc.pb.h"
#include "flexiv/pdk/mesh_operation/service.grpc.pb.h"
#include "flexiv/pdk/scene_event_service.grpc.pb.h"
#include "flexiv/pdk/scene/collision/collision_service.grpc.pb.h"
#include "flexiv/pdk/scene/reconstruction/service.grpc.pb.h"
#include "flexiv/pdk/system/components_service.grpc.pb.h"
#include "flexiv/pdk/system/kinematics_service.grpc.pb.h"
#include "flexiv/pdk/system/state_service.grpc.pb.h"
#include "flexiv/pdk/system/system_service.grpc.pb.h"
#include "flexiv/pdk/surface_finish/service.grpc.pb.h"
#include "flexiv/pdk/workcell/workcell_service.grpc.pb.h"
#include "flexiv/pdk/point_to_point_path/service.grpc.pb.h"

namespace flexiv {
namespace pdk {

template <typename ServiceT>
class ServiceClient
{
public:
  using StubType = typename ServiceT::Stub;

  explicit ServiceClient(const std::shared_ptr<grpc::Channel>& channel)
  : stub(ServiceT::NewStub(channel))
  {
  }

  std::unique_ptr<StubType> stub;
};

using VersionServiceClient = ServiceClient<::flexiv::pdk::common::VersionService>;
using LogServiceClient = ServiceClient<::flexiv::pdk::common::LogService>;
using FrameServiceClient = ServiceClient<::flexiv::pdk::FrameService>;
using SceneEventServiceClient = ServiceClient<::flexiv::pdk::SceneEventService>;
using WorkcellServiceClient = ServiceClient<::flexiv::pdk::workcell::WorkcellService>;
using CollisionServiceClient = ServiceClient<::flexiv::pdk::scene::collision::CollisionService>;
using ComponentsServiceClient = ServiceClient<::flexiv::pdk::system::ComponentsService>;
using StateServiceClient = ServiceClient<::flexiv::pdk::system::StateService>;
using SystemServiceClient = ServiceClient<::flexiv::pdk::system::SystemService>;
using KinematicsServiceClient = ServiceClient<::flexiv::pdk::system::KinematicsService>;
using SurfaceFinishServiceClient
    = ServiceClient<::flexiv::pdk::surface_finish::generator::SurfaceFinishService>;
using ConfigServiceClient = ServiceClient<::flexiv::pdk::ConfigService>;
class LicenseServiceClient : public ServiceClient<::flexiv::pdk::license::LicenseService>
{
public:
  using ServiceClient::ServiceClient;

  /**
   * @brief Install the .lic file Flexiv sent back. Takes effect immediately.
   *
   * The file is read here and its contents sent over gRPC, so the path is resolved on this
   * machine - the server may be another host or a container, and never opens it.
   *
   * @param path Path to the .lic file Flexiv sent.
   * @param[out] response Set to the server's reply. Check its status as with any other call: an
   *                      unverifiable license is reported there.
   * @param file_name Name to save it as on the server. Defaults to the file's own name, or the
   *                  license id where that name is not a plain one.
   * @return The gRPC status of the Save call.
   * @throw std::runtime_error The file cannot be read, or is empty.
   */
  grpc::Status InstallFile(const std::string& path, ::flexiv::pdk::license::SaveResponse* response,
      const std::string& file_name = "");
};
using PointToPointPathServiceClient
    = ServiceClient<::flexiv::pdk::point_to_point_path::PointToPointPathService>;
using MeshOperationServiceClient = ServiceClient<::flexiv::pdk::MeshOperationService>;
using CameraServiceClient = ServiceClient<::flexiv::pdk::camera::CameraService>;
using ReconstructionServiceClient
    = ServiceClient<::flexiv::pdk::scene::reconstruction::ReconstructionService>;

class Client
{
public:
  explicit Client(const std::string& target = "localhost:50052");
  explicit Client(std::shared_ptr<grpc::Channel> channel);
  ~Client() = default;

  Client(const Client&) = delete;
  Client& operator=(const Client&) = delete;
  Client(Client&&) = delete;
  Client& operator=(Client&&) = delete;

  VersionServiceClient& version();
  LogServiceClient& log();
  FrameServiceClient& frame();
  SceneEventServiceClient& scene_event();
  WorkcellServiceClient& workcell();
  CollisionServiceClient& collision();
  ComponentsServiceClient& system_config();
  StateServiceClient& system_state();
  SystemServiceClient& system();
  KinematicsServiceClient& kinematics();
  SurfaceFinishServiceClient& surface_finish();
  ConfigServiceClient& config();
  LicenseServiceClient& license();
  PointToPointPathServiceClient& point_to_point_path();
  MeshOperationServiceClient& mesh_operation();
  CameraServiceClient& camera();
  ReconstructionServiceClient& reconstruction();

  /**
   * @brief Ask the server whether this client works with it.
   * @param[out] message If not null, set to why not, or to the server version.
   * @return False when the versions are incompatible or the server cannot be reached.
   */
  bool CheckVersion(std::string* message = nullptr);

  std::shared_ptr<grpc::Channel> channel() const;
  void close();

private:
  template <typename ServiceClientT>
  ServiceClientT& LazyInit(std::unique_ptr<ServiceClientT>& service_client);

  std::shared_ptr<grpc::Channel> channel_;

  std::unique_ptr<VersionServiceClient> version_;
  std::unique_ptr<LogServiceClient> log_;
  std::unique_ptr<FrameServiceClient> frame_;
  std::unique_ptr<SceneEventServiceClient> scene_event_;
  std::unique_ptr<WorkcellServiceClient> workcell_;
  std::unique_ptr<CollisionServiceClient> collision_;
  std::unique_ptr<ComponentsServiceClient> system_config_;
  std::unique_ptr<StateServiceClient> system_state_;
  std::unique_ptr<SystemServiceClient> system_;
  std::unique_ptr<KinematicsServiceClient> kinematics_;
  std::unique_ptr<SurfaceFinishServiceClient> surface_finish_;
  std::unique_ptr<ConfigServiceClient> config_;
  std::unique_ptr<LicenseServiceClient> license_;
  std::unique_ptr<PointToPointPathServiceClient> point_to_point_path_;
  std::unique_ptr<MeshOperationServiceClient> mesh_operation_;
  std::unique_ptr<CameraServiceClient> camera_;
  std::unique_ptr<ReconstructionServiceClient> reconstruction_;

  mutable std::mutex mutex_;
};

} // namespace pdk
} // namespace flexiv

#endif
