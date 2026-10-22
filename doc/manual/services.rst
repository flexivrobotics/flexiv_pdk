Services
========

This page lists every gRPC service and RPC defined in ``proto/flexiv/pdk/``.
All RPCs are unary unless the response is marked *stream*. The ``.proto``
files are the authoritative definition; message fields are summarized in
:doc:`messages`.

``Empty`` is ``google.protobuf.Empty`` (``from google.protobuf.empty_pb2 import
Empty``). ``common.Status`` is ``flexiv.pdk.common.Status``, returned directly
by some RPCs instead of a wrapper response.

Request and response types without a package prefix are defined in the
service's own module. Several modules define messages with the same short name,
so import each from the right module, or alias them:

* ``NameRequest``, ``ExistsResponse``, ``RemoveResponse``, ``RenameRequest``,
  ``RenameResponse``: ``workcell_service`` and ``collision_service``.
* ``ListResponse``: ``workcell_service``, ``collision_service`` and
  ``license_service``.
* ``SaveRequest``, ``SaveResponse``: ``collision_service`` and
  ``license_service``.
* ``GetResponse``: ``collision_service`` and ``surface_finish.service``.
* ``GetUrdfResponse``: ``config_service`` and ``system_service``.
* ``ListComponentsResponse``: ``collision_service`` and
  ``components_service``.
* ``Path``: ``surface_finish.path`` and ``point_to_point_path.path``.

.. code-block:: python

   from flexiv.pdk.workcell.workcell_service_pb2 import NameRequest
   from flexiv.pdk.scene.collision.collision_service_pb2 import (
       NameRequest as CollisionNameRequest, SaveRequest as CollisionSaveRequest)

WorkcellService
---------------

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.workcell.WorkcellService``
   * - Proto file
     - ``flexiv/pdk/workcell/workcell_service.proto``
   * - Python module
     - ``flexiv.pdk.workcell.workcell_service_pb2`` (stub in ``flexiv.pdk.workcell.workcell_service_pb2_grpc``)
   * - Python client
     - ``client.workcell.stub``
   * - C++ client
     - ``client.workcell().stub``
   * - License
     - not required

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``Create``
     - ``CreateRequest``
     - ``CreateResponse``
     - Create an empty workcell.
   * - ``Load``
     - ``NameRequest``
     - ``WorkcellResponse``
     - Make a workcell active.
   * - ``Remove``
     - ``NameRequest``
     - ``RemoveResponse``
     - Delete a workcell and its contents.
   * - ``Rename``
     - ``RenameRequest``
     - ``RenameResponse``
     - 
   * - ``Exists``
     - ``NameRequest``
     - ``ExistsResponse``
     - 
   * - ``List``
     - ``google.protobuf.Empty``
     - ``ListResponse``
     - All workcells (full ``Workcell`` messages).
   * - ``GetActive``
     - ``google.protobuf.Empty``
     - ``WorkcellResponse``
     - The active workcell.
   * - ``SetDescription``
     - ``SetDescriptionRequest``
     - ``SetDescriptionResponse``
     - 

ConfigService
-------------

Saved scene configuration in the active workcell. Every RPC needs an active
workcell; without one the server rejects the call with ``FAILED_PRECONDITION``.
The parent and pose saved here are where an item starts each time the workcell
is loaded, and changing them also moves the item now. To read or move where an
item is right now without saving, use `FrameService`_.

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.ConfigService``
   * - Proto file
     - ``flexiv/pdk/config_service.proto``
   * - Python module
     - ``flexiv.pdk.config_service_pb2`` (stub in ``flexiv.pdk.config_service_pb2_grpc``)
   * - Python client
     - ``client.config.stub``
   * - C++ client
     - ``client.config().stub``
   * - License
     - not required

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``CheckReady``
     - ``CheckReadyRequest``
     - ``CheckReadyResponse``
     - Whether a config type can be used now (for example, a workcell is
       active). ``status.code`` is ``OK`` when ready, otherwise
       ``FAILED_PRECONDITION`` with the reason in ``status.message``.
   * - ``Exists``
     - ``TypeNameConfigRequest``
     - ``ExistsConfigResponse``
     - 
   * - ``Get``
     - ``TypeNameConfigRequest``
     - ``GetConfigResponse``
     - 
   * - ``List``
     - ``ListConfigRequest``
     - ``ListConfigResponse``
     - Names of all configs of a type.
   * - ``Remove``
     - ``TypeNameConfigRequest``
     - ``RemoveConfigResponse``
     - 
   * - ``Rename``
     - ``RenameConfigRequest``
     - ``RenameConfigResponse``
     - 
   * - ``Save``
     - ``SaveConfigRequest``
     - ``SaveConfigResponse``
     - Create or overwrite one config. Set one ``config`` field; see below.
   * - ``GetParent``
     - ``TypeNameConfigRequest``
     - ``GetParentResponse``
     - 
   * - ``SetParent``
     - ``SetParentRequest``
     - ``SetParentResponse``
     - 
   * - ``GetPose``
     - ``TypeNameConfigRequest``
     - ``GetPoseResponse``
     - Pose in parent.
   * - ``SetPose``
     - ``SetPoseRequest``
     - ``SetPoseResponse``
     - Persisted; emits a CONFIG scene event.
   * - ``GetUrdf``
     - ``google.protobuf.Empty``
     - ``GetUrdfResponse``
     - URDF of the whole scene.
   * - ``HasParent``
     - ``HasParentRequest``
     - ``HasParentResponse``
     - 
   * - ``HasChild``
     - ``HasChildRequest``
     - ``HasChildResponse``
     - 

``SaveConfigRequest`` and ``GetConfigResponse`` hold one ``config`` field. Each
field matches a ``ConfigType`` for the type-and-name RPCs:

.. list-table::
   :header-rows: 1
   :widths: 25 40 35

   * - ``config`` field
     - Message
     - ``ConfigType``
   * - ``coordinate``
     - ``scene.Coordinate``
     - ``CONFIG_TYPE_COORDINATE``
   * - ``camera``
     - ``scene.Camera``
     - ``CONFIG_TYPE_CAMERA``
   * - ``object``
     - ``scene.Object``
     - ``CONFIG_TYPE_OBJECT``
   * - ``system``
     - ``system.System``
     - ``CONFIG_TYPE_SYSTEM``
   * - ``surface_path``
     - ``surface_finish.Path``
     - ``CONFIG_TYPE_SURFACE_PATH``
   * - ``p2p_path``
     - ``point_to_point_path.Path``
     - ``CONFIG_TYPE_P2P_PATH``
   * - ``system_pose``
     - ``scene.TargetWaypoint``
     - ``CONFIG_TYPE_SYSTEM_POSE``
   * - ``object_pose``
     - ``scene.Coordinate``
     - ``CONFIG_TYPE_OBJECT_POSE``
   * - ``grasp_pose``
     - ``scene.Coordinate``
     - ``CONFIG_TYPE_GRASP_POSE``

``CONFIG_TYPE_ALL`` searches every type. See :doc:`messages` for the enum.

FrameService
------------

The scene as it is right now. Changes take effect immediately and are not
saved; reloading the workcell restores the saved state from `ConfigService`_.

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.FrameService``
   * - Proto file
     - ``flexiv/pdk/frame_service.proto``
   * - Python module
     - ``flexiv.pdk.frame_service_pb2`` (stub in ``flexiv.pdk.frame_service_pb2_grpc``)
   * - Python client
     - ``client.frame.stub``
   * - C++ client
     - ``client.frame().stub``
   * - License
     - not required

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``Exists``
     - ``ExistsFrameRequest``
     - ``ExistsFrameResponse``
     - 
   * - ``Get``
     - ``GetFrameRequest``
     - ``GetFrameResponse``
     - 
   * - ``List``
     - ``ListFramesRequest``
     - ``ListFramesResponse``
     - 
   * - ``Remove``
     - ``RemoveFrameRequest``
     - ``RemoveFrameResponse``
     - 
   * - ``Rename``
     - ``RenameFrameRequest``
     - ``RenameFrameResponse``
     - 
   * - ``GetParent``
     - ``GetFrameParentRequest``
     - ``GetFrameParentResponse``
     - 
   * - ``SetParent``
     - ``SetFrameParentRequest``
     - ``SetFrameParentResponse``
     - Takes a ``ParentingPolicy``.
   * - ``GetPose``
     - ``GetFramePoseRequest``
     - ``GetFramePoseResponse``
     - Pose in WORLD, PARENT or a NAMED frame.
   * - ``UpdatePose``
     - ``UpdateFramePoseRequest``
     - ``UpdateFramePoseResponse``
     - Transform layer only; not persisted.
   * - ``HasParent``
     - ``HasFrameParentRequest``
     - ``HasFrameParentResponse``
     - 
   * - ``HasChild``
     - ``HasFrameChildRequest``
     - ``HasFrameChildResponse``
     - 

SceneEventService
-----------------

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.SceneEventService``
   * - Proto file
     - ``flexiv/pdk/scene_event_service.proto``
   * - Python module
     - ``flexiv.pdk.scene_event_service_pb2`` (stub in ``flexiv.pdk.scene_event_service_pb2_grpc``)
   * - Python client
     - ``client.scene_event.stub``
   * - C++ client
     - ``client.scene_event().stub``
   * - License
     - not required

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``WatchSceneEvents``
     - ``WatchSceneEventsRequest``
     - stream ``SceneEvent``
     - Server-streaming. Ordered scene changes.

CollisionService
----------------

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.scene.collision.CollisionService``
   * - Proto file
     - ``flexiv/pdk/scene/collision/collision_service.proto``
   * - Python module
     - ``flexiv.pdk.scene.collision.collision_service_pb2`` (stub in ``flexiv.pdk.scene.collision.collision_service_pb2_grpc``)
   * - Python client
     - ``client.collision.stub``
   * - C++ client
     - ``client.collision().stub``
   * - License
     - not required

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``Get``
     - ``NameRequest``
     - ``GetResponse``
     - 
   * - ``Save``
     - ``SaveRequest``
     - ``SaveResponse``
     - 
   * - ``Remove``
     - ``NameRequest``
     - ``RemoveResponse``
     - 
   * - ``Rename``
     - ``RenameRequest``
     - ``RenameResponse``
     - 
   * - ``Exists``
     - ``NameRequest``
     - ``ExistsResponse``
     - 
   * - ``List``
     - ``google.protobuf.Empty``
     - ``ListResponse``
     - 
   * - ``AddPair``
     - ``AddPairRequest``
     - ``AddPairResponse``
     - Add one allowed (unchecked) pair to a saved config.
   * - ``RemovePair``
     - ``RemovePairRequest``
     - ``RemovePairResponse``
     - Remove one allowed pair, so it is checked again.
   * - ``ListComponents``
     - ``google.protobuf.Empty``
     - ``ListComponentsResponse``
     - Valid names for collision pairs.

SystemService
-------------

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.system.SystemService``
   * - Proto file
     - ``flexiv/pdk/system/system_service.proto``
   * - Python module
     - ``flexiv.pdk.system.system_service_pb2`` (stub in ``flexiv.pdk.system.system_service_pb2_grpc``)
   * - Python client
     - ``client.system.stub``
   * - C++ client
     - ``client.system().stub``
   * - License
     - not required

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``AddConnectedSystem``
     - ``AddConnectedSystemRequest``
     - ``AddConnectedSystemResponse``
     - Read a real robot's configuration and save it as a system.
   * - ``GetCalibrationStatus``
     - ``GetCalibrationStatusRequest``
     - ``GetCalibrationStatusResponse``
     - Whether a calibration exists and was applied.
   * - ``GetUrdf``
     - ``GetUrdfRequest``
     - ``GetUrdfResponse``
     - URDF of one system.
   * - ``GetArmSerialNumber``
     - ``GetArmSerialNumberRequest``
     - ``GetArmSerialNumberResponse``
     - 

SystemService has no joint-position RPCs. A system's default joint position is
the ``home_position`` of its components, saved in its ``System`` config through
`ConfigService`_. Its current joint position is in `StateService`_.

ComponentsService
-----------------

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.system.ComponentsService``
   * - Proto file
     - ``flexiv/pdk/system/components_service.proto``
   * - Python module
     - ``flexiv.pdk.system.components_service_pb2`` (stub in ``flexiv.pdk.system.components_service_pb2_grpc``)
   * - Python client
     - ``client.system_config.stub``
   * - C++ client
     - ``client.system_config().stub``
   * - License
     - not required

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``ListManipulators``
     - ``google.protobuf.Empty``
     - ``ListComponentsResponse``
     - Returns ``names``.
   * - ``ListToolAdapters``
     - ``google.protobuf.Empty``
     - ``ListManufacturerModelResponse``
     - 
   * - ``ListTools``
     - ``google.protobuf.Empty``
     - ``ListManufacturerModelResponse``
     - 
   * - ``ListCustomToolAdapters``
     - ``google.protobuf.Empty``
     - ``ListManufacturerModelResponse``
     - 
   * - ``ListCustomTools``
     - ``google.protobuf.Empty``
     - ``ListManufacturerModelResponse``
     - 
   * - ``ListExternalRobotAxes``
     - ``google.protobuf.Empty``
     - ``ListManufacturerModelResponse``
     - 
   * - ``ListExternalWorkpieceAxes``
     - ``google.protobuf.Empty``
     - ``ListManufacturerModelResponse``
     - 
   * - ``SaveCustomTool``
     - ``SaveCustomToolRequest``
     - ``SaveCustomToolResponse``
     - Add to the custom tool catalogue.
   * - ``SaveCustomToolAdapter``
     - ``SaveCustomToolAdapterRequest``
     - ``SaveCustomToolAdapterResponse``
     - Add to the custom adapter catalogue.
   * - ``RemoveCustomTool``
     - ``ManufacturerModel``
     - ``RemoveCustomToolResponse``
     - 
   * - ``RemoveCustomToolAdapter``
     - ``ManufacturerModel``
     - ``RemoveCustomToolAdapterResponse``
     - 

StateService
------------

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.system.StateService``
   * - Proto file
     - ``flexiv/pdk/system/state_service.proto``
   * - Python module
     - ``flexiv.pdk.system.state_service_pb2`` (stub in ``flexiv.pdk.system.state_service_pb2_grpc``)
   * - Python client
     - ``client.system_state.stub``
   * - C++ client
     - ``client.system_state().stub``
   * - License
     - not required

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``GetJointPosition``
     - ``GetJointPositionRequest``
     - ``GetJointPositionResponse``
     - *Current* joint position (scene model, not the real robot).
   * - ``SetJointPosition``
     - ``SetJointPositionRequest``
     - ``SetJointPositionResponse``
     - *Current* joint position (scene model, not the real robot). Not saved;
       a system starts at its saved ``home_position``.

KinematicsService
-----------------

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.system.KinematicsService``
   * - Proto file
     - ``flexiv/pdk/system/kinematics_service.proto``
   * - Python module
     - ``flexiv.pdk.system.kinematics_service_pb2`` (stub in ``flexiv.pdk.system.kinematics_service_pb2_grpc``)
   * - Python client
     - ``client.kinematics.stub``
   * - C++ client
     - ``client.kinematics().stub``
   * - License
     - not required

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``ComputeIK``
     - ``IKRequest``
     - ``IKResponse``
     - Needs a collision config name.
   * - ``ComputeFK``
     - ``FKRequest``
     - ``FKResponse``
     - 

PointToPointPathService
-----------------------

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.point_to_point_path.PointToPointPathService``
   * - Proto file
     - ``flexiv/pdk/point_to_point_path/service.proto``
   * - Python module
     - ``flexiv.pdk.point_to_point_path.service_pb2`` (stub in ``flexiv.pdk.point_to_point_path.service_pb2_grpc``)
   * - Python client
     - ``client.point_to_point_path.stub``
   * - C++ client
     - ``client.point_to_point_path().stub``
   * - License
     - required, license code ``point_to_point_path``

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``Plan``
     - ``PointToPointPathRequest``
     - ``PointToPointPathResponse``
     - Result saved as a ``CONFIG_TYPE_P2P_PATH`` config.

SurfaceFinishService
--------------------

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.surface_finish.generator.SurfaceFinishService``
   * - Proto file
     - ``flexiv/pdk/surface_finish/service.proto``
   * - Python module
     - ``flexiv.pdk.surface_finish.service_pb2`` (stub in ``flexiv.pdk.surface_finish.service_pb2_grpc``)
   * - Python client
     - ``client.surface_finish.stub``
   * - C++ client
     - ``client.surface_finish().stub``
   * - License
     - required, license code ``surface_finish``

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``GenerateNominalPath``
     - ``GenerateNominalPathRequest``
     - ``GenerateNominalPathResponse``
     - Stage 1. May create several paths.
   * - ``RefinePath``
     - ``RefinePathRequest``
     - ``RefinePathResponse``
     - Stage 2.
   * - ``CreateRobotMotion``
     - ``CreateRobotMotionRequest``
     - ``CreateRobotMotionResponse``
     - Stage 3.
   * - ``Get``
     - ``GetRequest``
     - ``GetResponse``
     - All stages' data.
   * - ``GenerateRCATrajectoryFile``
     - ``GenerateRCATrajectoryFileRequest``
     - ``GenerateRCATrajectoryFileResponse``
     - Writes a ``.traj`` file on the server.

MeshOperationService
--------------------

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.MeshOperationService``
   * - Proto file
     - ``flexiv/pdk/mesh_operation/service.proto``
   * - Python module
     - ``flexiv.pdk.mesh_operation.service_pb2`` (stub in ``flexiv.pdk.mesh_operation.service_pb2_grpc``)
   * - Python client
     - ``client.mesh_operation.stub``
   * - C++ client
     - ``client.mesh_operation().stub``
   * - License
     - required, license code ``mesh_operation``

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``ExtractArea``
     - ``AreaExtractionRequest``
     - ``AreaExtractionResponse``
     - Polygon cut-out saved as a new object.
   * - ``FilterMesh``
     - ``FilterMeshRequest``
     - ``FilterMeshResponse``
     - One filter; results saved as new objects.

CameraService
-------------

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.camera.CameraService``
   * - Proto file
     - ``flexiv/pdk/camera/service.proto``
   * - Python module
     - ``flexiv.pdk.camera.service_pb2`` (stub in ``flexiv.pdk.camera.service_pb2_grpc``)
   * - Python client
     - ``client.camera.stub``
   * - C++ client
     - ``client.camera().stub``
   * - License
     - not required

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``IsCameraOnline``
     - ``CameraNameRequest``
     - ``CameraOnlineResponse``
     - Whether the device responds.
   * - ``UpdateCameraIntrinsicFromDevice``
     - ``CameraNameRequest``
     - ``UpdateCameraIntrinsicFromDeviceResponse``
     - Read and store fx, fy, cx, cy, distortion.
   * - ``GetCameraRGBDImage``
     - ``CameraRGBDImageRequest``
     - ``CameraRGBDImageResponse``
     - Saved on the server if a file name is given.
   * - ``GetCameraPointCloud``
     - ``CameraPointCloudRequest``
     - ``CameraPointCloudResponse``
     - Camera or world frame; saved on the server.
   * - ``ListSavedCameraImages``
     - ``CameraNameRequest``
     - ``CameraImageListResponse``
     - 
   * - ``ListSavedCameraPointClouds``
     - ``CameraNameRequest``
     - ``CameraPointCloudListResponse``
     - 
   * - ``DeleteSavedCameraImage``
     - ``CameraImageDeleteRequest``
     - ``common.Status``
     - 
   * - ``DeleteSavedCameraPointCloud``
     - ``CameraPointCloudDeleteRequest``
     - ``common.Status``
     - 

ReconstructionService
---------------------

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.scene.reconstruction.ReconstructionService``
   * - Proto file
     - ``flexiv/pdk/scene/reconstruction/service.proto``
   * - Python module
     - ``flexiv.pdk.scene.reconstruction.service_pb2`` (stub in ``flexiv.pdk.scene.reconstruction.service_pb2_grpc``)
   * - Python client
     - ``client.reconstruction.stub``
   * - C++ client
     - ``client.reconstruction().stub``
   * - License
     - not required

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``StartReconstruction``
     - ``StartReconstructionRequest``
     - ``common.Status``
     - 
   * - ``AddCameraToReconstruction``
     - ``CameraNamesRequest``
     - ``common.Status``
     - 
   * - ``RemoveCameraFromReconstruction``
     - ``CameraNamesRequest``
     - ``common.Status``
     - 
   * - ``StopReconstruction``
     - ``google.protobuf.Empty``
     - ``common.Status``
     - 
   * - ``GetReconstructionResult``
     - ``ReconstructionResultRequest``
     - ``ReconstructionResultResponse``
     - Optionally adds the result to the scene.
   * - ``ListReconstructionObjects``
     - ``google.protobuf.Empty``
     - ``ListReconstructionObjectsResponse``
     - 
   * - ``AddReconstructionConfig``
     - ``ReconstructionConfig``
     - ``common.Status``
     - 
   * - ``RemoveReconstructionConfig``
     - ``ReconstructionConfig``
     - ``common.Status``
     - 
   * - ``GetReconstructionConfig``
     - ``GetReconstructionConfigRequest``
     - ``GetReconstructionConfigResponse``
     - 
   * - ``ListReconstructionConfigs``
     - ``google.protobuf.Empty``
     - ``ListReconstructionConfigsResponse``
     - 

LicenseService
--------------

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.license.LicenseService``
   * - Proto file
     - ``flexiv/pdk/license/license_service.proto``
   * - Python module
     - ``flexiv.pdk.license.license_service_pb2`` (stub in ``flexiv.pdk.license.license_service_pb2_grpc``)
   * - Python client
     - ``client.license.stub``
   * - C++ client
     - ``client.license().stub``
   * - License
     - not required

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``List``
     - ``ListRequest``
     - ``ListResponse``
     - Every licensable service and its state.
   * - ``Save``
     - ``SaveRequest``
     - ``SaveResponse``
     - Install a license; effective immediately.
   * - ``GetDeviceIdentifier``
     - ``GetDeviceIdentifierRequest``
     - ``GetDeviceIdentifierResponse``
     - Identifier to send to Flexiv.

VersionService
--------------

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.common.VersionService``
   * - Proto file
     - ``flexiv/pdk/common/version_service.proto``
   * - Python module
     - ``flexiv.pdk.common.version_service_pb2`` (stub in ``flexiv.pdk.common.version_service_pb2_grpc``)
   * - Python client
     - ``client.version.stub``
   * - C++ client
     - ``client.version().stub``
   * - License
     - not required

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``GetVersion``
     - ``GetVersionRequest``
     - ``GetVersionResponse``
     - Server version and ``compatible`` flag.

LogService
----------

.. list-table::
   :widths: 25 75

   * - gRPC name
     - ``flexiv.pdk.common.LogService``
   * - Proto file
     - ``flexiv/pdk/common/log_service.proto``
   * - Python module
     - ``flexiv.pdk.common.log_service_pb2`` (stub in ``flexiv.pdk.common.log_service_pb2_grpc``)
   * - Python client
     - ``client.log.stub``
   * - C++ client
     - ``client.log().stub``
   * - License
     - not required

.. list-table::
   :header-rows: 1
   :widths: 24 28 28 20

   * - RPC
     - Request
     - Response
     - Notes
   * - ``SetLogLevel``
     - ``SetLogLevelRequest``
     - ``SetLogLevelResponse``
     - Minimum server log level.
   * - ``GetLogHistory``
     - ``GetLogHistoryRequest``
     - ``GetLogHistoryResponse``
     - Recent entries, oldest first. Filter by level, count and time.
   * - ``StreamLogEntries``
     - ``StreamLogEntriesRequest``
     - stream ``LogEntry``
     - Server-streaming log entries.

