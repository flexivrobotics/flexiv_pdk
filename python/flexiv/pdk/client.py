import grpc


class LicenseServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.license.license_service_pb2_grpc as license_grpc

        self.stub = license_grpc.LicenseServiceStub(channel)

    def install_file(self, path, file_name: str = ""):
        """Install the .lic file Flexiv sent back. Takes effect immediately.

        The file is read here and its contents sent over gRPC, so the path is
        resolved on this machine - the server may be another host or a
        container, and never opens it.

        Args:
          path: Path to the `.lic` file Flexiv sent.
          file_name: Name to save it as on the server. Defaults to the file's
            own name, or the license id where that name is not a plain one.

        Returns:
          The `SaveResponse`. Check `status.code` as with any other call: an
          unverifiable license is reported there, not raised.

        Raises:
          OSError: The file cannot be read.
          ValueError: The file is empty.
        """
        from flexiv.pdk.license.license_file import (
            read_license_file,
            server_file_name,
        )
        from flexiv.pdk.license.license_service_pb2 import SaveRequest

        return self.stub.Save(SaveRequest(
            license=read_license_file(path),
            file_name=file_name or server_file_name(path)))


class VersionServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.common.version_service_pb2_grpc as version_grpc

        self.stub = version_grpc.VersionServiceStub(channel)


class LogServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.common.log_service_pb2_grpc as log_grpc

        self.stub = log_grpc.LogServiceStub(channel)


class FrameServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.frame_service_pb2_grpc as frame_grpc

        self.stub = frame_grpc.FrameServiceStub(channel)


class SceneEventServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.scene_event_service_pb2_grpc as scene_event_grpc

        self.stub = scene_event_grpc.SceneEventServiceStub(channel)


class WorkcellServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.workcell.workcell_service_pb2_grpc as workcell_grpc

        self.stub = workcell_grpc.WorkcellServiceStub(channel)


class CollisionServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.scene.collision.collision_service_pb2_grpc as collision_grpc

        self.stub = collision_grpc.CollisionServiceStub(channel)


class ComponentsServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.system.components_service_pb2_grpc as sys_config_grpc

        self.stub = sys_config_grpc.ComponentsServiceStub(channel)


class StateServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.system.state_service_pb2_grpc as sys_state_grpc

        self.stub = sys_state_grpc.StateServiceStub(channel)


class SystemServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.system.system_service_pb2_grpc as system_grpc

        self.stub = system_grpc.SystemServiceStub(channel)


class SurfaceFinishServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.surface_finish.service_pb2_grpc as surface_grpc

        self.stub = surface_grpc.SurfaceFinishServiceStub(channel)


class ConfigServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.config_service_pb2_grpc as config_grpc

        self.stub = config_grpc.ConfigServiceStub(channel)


class KinematicsServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.system.kinematics_service_pb2_grpc as kinematics_grpc

        self.stub = kinematics_grpc.KinematicsServiceStub(channel)


class PointToPointPathServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.point_to_point_path.service_pb2_grpc as ptp_path_grpc
        self.stub = ptp_path_grpc.PointToPointPathServiceStub(channel)


class MeshOperationServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.mesh_operation.service_pb2_grpc as mesh_op_grpc
        self.stub = mesh_op_grpc.MeshOperationServiceStub(channel)


class CameraServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.camera.service_pb2_grpc as camera_grpc
        self.stub = camera_grpc.CameraServiceStub(channel)


class ReconstructionServiceClient:
    def __init__(self, channel: grpc.Channel):
        import flexiv.pdk.scene.reconstruction.service_pb2_grpc as reconstruction_grpc
        self.stub = reconstruction_grpc.ReconstructionServiceStub(channel)


class Client:
    """
    Main client class that encapsulates all major gRPC services.
    """
    def __init__(self, target: str = "localhost:50052"):
        self.channel = grpc.insecure_channel(target)
        self._license = None
        self._version = None
        self._log = None
        self._frame = None
        self._scene_event = None
        self._workcell = None
        self._collision = None
        self._system_config = None
        self._system_state = None
        self._system = None
        self._surface_finish = None
        self._config = None
        self._kinematics = None

        self._point_to_point_path = None
        self._mesh_operation = None
        self._camera = None
        self._reconstruction = None

    @property
    def license(self):
        if self._license is None:
            self._license = LicenseServiceClient(self.channel)
        return self._license

    @property
    def version(self):
        if self._version is None:
            self._version = VersionServiceClient(self.channel)
        return self._version

    @property
    def log(self):
        if self._log is None:
            self._log = LogServiceClient(self.channel)
        return self._log

    @property
    def frame(self):
        if self._frame is None:
            self._frame = FrameServiceClient(self.channel)
        return self._frame

    @property
    def scene_event(self):
        if self._scene_event is None:
            self._scene_event = SceneEventServiceClient(self.channel)
        return self._scene_event

    @property
    def workcell(self):
        if self._workcell is None:
            self._workcell = WorkcellServiceClient(self.channel)
        return self._workcell

    @property
    def collision(self):
        if self._collision is None:
            self._collision = CollisionServiceClient(self.channel)
        return self._collision

    @property
    def system_config(self):
        if self._system_config is None:
            self._system_config = ComponentsServiceClient(self.channel)
        return self._system_config

    @property
    def system_state(self):
        if self._system_state is None:
            self._system_state = StateServiceClient(self.channel)
        return self._system_state

    @property
    def system(self):
        if self._system is None:
            self._system = SystemServiceClient(self.channel)
        return self._system

    @property
    def surface_finish(self):
        if self._surface_finish is None:
            self._surface_finish = SurfaceFinishServiceClient(self.channel)
        return self._surface_finish

    @property
    def config(self):
        if self._config is None:
            self._config = ConfigServiceClient(self.channel)
        return self._config

    @property
    def kinematics(self):
        if self._kinematics is None:
            self._kinematics = KinematicsServiceClient(self.channel)
        return self._kinematics
    
    @property
    def point_to_point_path(self):
        if self._point_to_point_path is None:
            self._point_to_point_path = PointToPointPathServiceClient(self.channel)
        return self._point_to_point_path

    @property
    def mesh_operation(self):
        if self._mesh_operation is None:
            self._mesh_operation = MeshOperationServiceClient(self.channel)
        return self._mesh_operation

    @property
    def camera(self):
        if self._camera is None:
            self._camera = CameraServiceClient(self.channel)
        return self._camera

    @property
    def reconstruction(self):
        if self._reconstruction is None:
            self._reconstruction = ReconstructionServiceClient(self.channel)
        return self._reconstruction

    def check_version(self):
        """Ask the server whether this client works with it.

        Returns:
          A tuple `(compatible, message)`. `message` says why not, or gives
          the server version. `compatible` is False when the server cannot be
          reached.
        """
        import re

        from flexiv.pdk import __version__
        from flexiv.pdk.common.version_pb2 import Version
        from flexiv.pdk.common.version_service_pb2 import GetVersionRequest

        major, minor, patch = (
            int(part) for part in re.match(r"(\d+)\.(\d+)\.(\d+)", __version__).groups())
        try:
            response = self.version.stub.GetVersion(GetVersionRequest(
                client_version=Version(major=major, minor=minor, patch=patch)))
        except grpc.RpcError as error:
            return False, f"Cannot get the server version: {error.details()}"
        server = response.server_version
        server_version = f"{server.major}.{server.minor}.{server.patch}"
        if response.compatible:
            return True, f"Server version {server_version}"
        return False, (
            f"Client {__version__} does not work with server {server_version}. "
            "Use a client and server with the same major and minor version.")

    def close(self):
        self.channel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
