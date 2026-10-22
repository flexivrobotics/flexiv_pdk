Messages
========

The messages you build most often, grouped by proto package. Field numbers are
omitted. *req* follows each field the ``.proto`` documents as required. The
``.proto`` files in ``proto/flexiv/pdk/`` are authoritative.

common
------

Module ``flexiv.pdk.common.*_pb2``.

``Status`` (``status_pb2``)
   ``code`` (``Code``: ``OK`` 0, ``NOT_FOUND`` 1, ``INVALID_ARGUMENT`` 2,
   ``INTERNAL_ERROR`` 3, ``FAILED_PRECONDITION`` 4, ``PERMISSION_DENIED`` 5),
   ``message`` (optional). See :doc:`/error_handling`.

``Version`` (``version_pb2``)
   ``major``, ``minor``, ``patch``.

``LogEntry`` (``log_entry_pb2``)
   ``timestamp``, ``level`` (``LogEntry.Level``: ``DEBUG``, ``INFO``,
   ``WARNING``, ``ERROR``), ``source``, ``message``.

``SetLogLevelRequest`` (``log_service_pb2``)
   ``level`` (``LogEntry.Level``).

``GetLogHistoryRequest`` (``log_service_pb2``)
   ``min_level`` (default ``DEBUG``, every entry), ``max_entries`` (newest
   entries to return; default all the server has kept), ``since``
   (``Timestamp``; default no limit).

``GetLogHistoryResponse`` (``log_service_pb2``)
   ``status``, ``entries[]`` (``LogEntry``, oldest first).

``StreamLogEntriesRequest`` (``log_service_pb2``)
   ``min_level`` (default ``DEBUG``).

``ExternalRobotAxis`` (enum, ``solver_options_pb2``)
   ``EXTERNAL_ROBOT_NONE`` (no external robot axis), ``EXTERNAL_ROBOT_PRESET``
   (fixed position for all waypoints), ``EXTERNAL_ROBOT_PREFERRED`` (preferred
   position).

``ExternalWorkpieceAxis`` (enum, ``solver_options_pb2``)
   ``EXTERNAL_WORKPIECE_NONE``, ``EXTERNAL_WORKPIECE_NOT_USED`` (not part of the
   planning group), ``EXTERNAL_WORKPIECE_PRESET``, ``EXTERNAL_WORKPIECE_PREFERRED``.

spatial
-------

Module ``flexiv.pdk.spatial.*_pb2``.

``Vector3`` (``geometry_pb2``)
   ``x``, ``y``, ``z``.

``Quaternion`` (``geometry_pb2``)
   ``x``, ``y``, ``z``, ``w``. Set ``w=1`` for identity.

``SE3Pose`` (``geometry_pb2``)
   ``position`` (``Vector3``, m), ``rotation`` (``Quaternion``).

``Wrench`` (``geometry_pb2``)
   ``force`` (N), ``torque`` (Nm), both ``Vector3``.

``Frame`` (``frame_pb2``)
   ``type`` (``FrameType``), ``pose_world``, ``pose_parent``, ``parent``,
   ``children``.

``FrameType``, ``ParentingPolicy``, ``ReferenceFrame`` (enums, ``frame_defs_pb2``)
   See :doc:`/scene_model`.

``Shape`` (``shape_pb2``)
   One of ``box`` (``Box.size`` = [x, y, z] m), ``capsule`` / ``cylinder``
   (``radius``, ``length``), ``sphere`` (``radius``), ``mesh`` / ``convex_mesh``
   (``filename``, ``scale`` *req*, use [1,1,1]), ``octomap`` (``filename``,
   ``resolution``).

``Visual`` (``shape_pb2``)
   ``origin`` *req* (``SE3Pose``), ``shape`` *req*, ``material_name``
   (default ``material.name``), ``material`` (``Material``; default the
   viewer's own color).

``Material`` (``shape_pb2``)
   ``name`` (default chosen by the server), ``rgba[]`` *req* (red, green, blue,
   alpha, each in [0, 1]), ``texture`` (not supported yet).

``Collision`` (``shape_pb2``)
   ``origin`` (``SE3Pose``), ``shape``.

``CartesianWaypoint`` (``waypoint_pb2``)
   ``pose``, ``velocity``, ``acceleration``, ``wrench`` (force/torque to apply
   in contact), ``null_space``.

``NullSpace`` (``waypoint_pb2``)
   ``elbow_swivel_angle`` (rad), ``external_robot_position``,
   ``external_workpiece_position``.

``JointWaypoint`` (``waypoint_pb2``)
   ``position``, ``velocity`` (repeated, one per joint).

physics
-------

Module ``flexiv.pdk.physics.properties_pb2``.

``Inertial``
   ``origin`` (centre of mass and principal axes), ``mass`` (kg), ``inertia``.

``Inertia``
   ``ixx``, ``iyy``, ``izz``, ``ixy``, ``ixz``, ``iyz`` (kg·m², about the COM).

Root package and scene
----------------------

``ConfigHeader`` (``flexiv.pdk.config_header_pb2``)
   ``name`` *req*, ``parent`` *req*, ``pose_in_parent`` *req*.

``Object`` (``flexiv.pdk.scene.object_pb2``)
   ``header`` *req*, ``inertial``, ``collision[]``, ``visual[]``,
   ``reference_only``.

``Camera`` (``flexiv.pdk.scene.camera_pb2``)
   ``header``, ``far_width`` *req*, ``far_height`` *req*, ``far_distance``
   *req*, ``near_distance`` *req* (m), ``depth_scale`` *req* (raw depth value to
   m), ``camera_id`` *req*.

``Coordinate`` (``flexiv.pdk.scene.coordinate_pb2``)
   ``header`` *req*, ``scale`` (``Vector3``, display size in m).

``TargetWaypoint`` (``flexiv.pdk.scene.target_waypoint_pb2``)
   A *system pose*: ``header``, ``tcp_name``, ``cartesian``
   (``CartesianWaypoint``), ``joint`` (``JointWaypoint``).

``CollisionConfig`` (``flexiv.pdk.scene.collision.collision_config_pb2``)
   ``name`` *req*, ``pairs[]`` (``CollisionPair(name1, name2)``, pairs allowed
   to collide and not checked; empty checks every pair), ``collision_margin``
   *req* (m). See :doc:`/collision`.

``ReconstructionConfig`` (``flexiv.pdk.scene.reconstruction.config_pb2``)
   ``name`` *req*, ``point_cloud_size`` *req* (e.g. 1000000), ``voxel_size``
   *req* (e.g. 0.005 m), ``voxel_bucket_count`` *req* (e.g. 10000).

``ConfigType`` (enum, ``flexiv.pdk.config_service_pb2``)
   ``CONFIG_TYPE_ALL`` (0, search every type; slower), ``CONFIG_TYPE_CAMERA``,
   ``CONFIG_TYPE_COORDINATE``, ``CONFIG_TYPE_SURFACE_PATH``,
   ``CONFIG_TYPE_OBJECT``, ``CONFIG_TYPE_P2P_PATH``, ``CONFIG_TYPE_SYSTEM``,
   ``CONFIG_TYPE_SYSTEM_POSE``, ``CONFIG_TYPE_OBJECT_POSE``,
   ``CONFIG_TYPE_GRASP_POSE``. See :doc:`services` for the message each one
   saves.

``SceneEvent`` (``flexiv.pdk.scene_event_service_pb2``)
   ``change``, ``origin``, ``entity`` (``EntityRef(type, name)``), ``frames[]``,
   ``new_name``. See :doc:`/scene_events`.

workcell
--------

``Workcell`` (``flexiv.pdk.workcell.workcell_pb2``)
   ``name``, ``description``, ``created``, ``updated`` (timestamps set by the
   server).

system
------

``System`` (``flexiv.pdk.system.system_pb2``)
   ``header`` *req*, ``control_box_serial_number`` *req*,
   ``external_robot_axis``, ``manipulator_adapter``, ``manipulator`` *req*,
   ``wrist_sensor``, ``tool_adapter``, ``tool[]``, ``external_workpiece[]``.
   See :doc:`/systems_and_components`.

``DualArmSystem`` (``flexiv.pdk.system.dual_arm_system_pb2``)
   ``header`` *req*, ``control_box_serial_number`` *req*,
   ``external_robot_axis`` *req* (torso or fixture with two flanges),
   ``left_arm`` *req*, ``left_wrist_sensor``, ``left_tool_adapter``,
   ``left_tool[]``, ``right_arm`` *req*, ``right_wrist_sensor``,
   ``right_tool_adapter``, ``right_tool[]``, ``remove_arm_base_link``,
   ``external_workpiece[]``. Defined in the ``.proto`` only:
   ``SaveConfigRequest`` has no field for it and no RPC takes it.

Components, module ``flexiv.pdk.system.components.<name>_pb2``:

``Manipulator`` (``manipulator_pb2``)
   ``name`` *req*, ``arm_serial_number`` *req*, ``lower_limit[]``,
   ``upper_limit[]``, ``home_position[]`` (rad).

``Adapter`` (``adapter_pb2``)
   ``name`` *req*, ``mass``, ``inertia[]``, ``xyz[]`` (m), ``rpy[]`` (rad),
   ``parent_flange_name``.

``ToolAdapter`` (``tool_adapter_pb2``)
   ``name`` *req*, ``manufacturer`` *req*, ``model`` *req*, ``rotation`` (rad).

``Tool`` (``tool_pb2``)
   ``name`` *req*, ``manufacturer`` *req*, ``model`` *req*,
   ``home_position[]``.

``WristSensor`` (``wrist_sensor_pb2``)
   ``name`` *req*, ``manufacturer`` *req*, ``model`` *req*,
   ``parameter_name``.

``ExternalAxis`` (``external_axis_pb2``)
   ``name`` *req*, ``manufacturer`` *req*, ``model`` *req*, ``amplifier_model``,
   ``rail_length[]`` (m), ``position_lower_limit[]``, ``position_upper_limit[]``,
   ``velocity_limit[]``, ``effort_limit[]``, ``home_position[]``,
   ``apply_calibration``, ``position_offset[]``.

``ExternalWorkpiece`` (``external_workpiece_pb2``)
   ``axis`` *req*, ``mount`` *req* (``Adapter``), ``tool_adapter``, ``tool[]``.

``CustomTool`` (``custom_tool_pb2``)
   ``manufacturer`` *req*, ``model`` *req*, ``tcp`` *req*, ``inertial``,
   ``collision[]``, ``visual[]``.

``CustomToolAdapter`` (``custom_tool_adapter_pb2``)
   ``manufacturer`` *req*, ``model`` *req*, ``flange[]`` *req*, ``inertial``,
   ``collision[]``, ``visual[]``.

``JointGroup`` (enum, ``joint_group_pb2``)
   ``JOINT_GROUP_SYSTEM`` (all actuated joints), ``JOINT_GROUP_ARM``,
   ``JOINT_GROUP_EXTERNAL_ROBOT_AXIS``, ``JOINT_GROUP_EXTERNAL_WORKPIECE_AXIS``.

point_to_point_path
-------------------

``PointToPointPathRequest`` (``flexiv.pdk.point_to_point_path.service_pb2``)
   ``path_name`` *req*, ``collision_config_name`` *req*; one of
   ``joint_waypoints`` (``PTPJointWaypoints(system_name, tcp_name,
   joint_waypoints[])``) or ``target_waypoints``
   (``PTPTargetWaypoints(target_waypoint_names[])``).

``Path`` (``flexiv.pdk.point_to_point_path.path_pb2``, output)
   ``header``, ``system_name``, ``tcp_name``, ``collision_config_name``,
   ``tcp_to_attach_object``, ``object_grasp_pose``, ``cartesian_waypoints[]``,
   ``joint_waypoints[]``.

surface_finish
--------------

Module ``flexiv.pdk.surface_finish.*_pb2``. The service's request and response
messages are in ``flexiv.pdk.surface_finish.service_pb2``; generator messages in
``flexiv.pdk.surface_finish.generator.<name>_pb2``.

``Path`` (``path_pb2``, output)
   ``header``; generator used (``manual_path``, ``edge_path``,
   ``surface_scan_path``, ``surface_sketch_path``, ``mesh_raster_path``,
   ``mesh_sketch_path``); ``refinement``; ``solver_preferences``;
   ``nominal_cartesian[]`` (stage 1); ``refined_cartesian[]`` (stage 2);
   ``basic_solution[]`` / ``advanced_solution[]`` (stage 3, ``JointWaypoint``).

``PathRefinement`` (``path_refinement_pb2``)
   ``reversed_order``, ``align_with_previous``, ``rotation_offset``,
   ``position_offset``. Applied in that order.

``SolverPreferences`` (``solver_preferences_pb2``)
   ``system_name`` *req*, ``tcp_ecp_name`` *req*, ``solver_type`` *req*
   (``SOLVER_TYPE_BASIC``, ``SOLVER_TYPE_ADVANCED``), ``null_space`` *req*,
   ``external_robot_axis``, ``external_workpiece_axis``, ``tool_symmetry``,
   ``tcp_to_attach_object``, ``object_grasp_pose``, ``joint_position_seed[]``.

Generators (``generator.*``):

``ManualPath``
   ``cartesian[]`` relative to the parent.

``MeshSketchPath``
   ``mesh_filename``, ``points[]`` (parent frame, on the surface),
   ``blending_radius``; spacing ``fixed_spacing`` | ``variable_spacing``;
   orientation ``align_with_initial_direction`` | ``align_with_previous`` |
   ``align_with_direction``.

``MeshRasterPath``
   ``mesh_filename``, ``fixed_spacing``, ``blending_radius``,
   ``polygon_border``, ``border_offset``, ``raster_line_spacing``,
   ``raster_path_joining_distance_threshold``; direction
   ``principal_rotation_angle`` | ``specified_direction``;
   ``minimum_toolpath_length``; orientation as for ``MeshSketchPath``.

``EdgePath``
   ``cad_filename``, ``edges[]``, ``faces[]``; spacing
   ``fixed_spacing`` | ``variable_spacing``.

``FaceRasterPath``
   ``cad_filename``, ``raster_line_spacing``, ``raster_rotation``,
   ``raster_flip``, ``start_position``, ``gap_tolerance_on_face``,
   ``gap_tolerance_between_faces``, ``faces[]``; spacing; border
   ``edge_border`` | ``polygon_border``.

``FaceSketchPath``
   ``cad_filename``, ``points[]``, ``faces[]``; spacing.

``VariableSpacing``
   ``min_spacing``, ``max_spacing``, ``position_tolerance``,
   ``orientation_tolerance``.

``EdgeBorder`` / ``PolygonBorder``
   ``width[]`` and ``edges[]`` / ``points[]``.

mesh_operation
--------------

``AreaExtractionRequest`` (``flexiv.pdk.mesh_operation.service_pb2``)
   ``object_name``, ``extracted_object_name``, ``mesh_filename``,
   ``boundary[]`` (on the surface, 1 mm tolerance).

``FilterMeshRequest`` (``flexiv.pdk.mesh_operation.service_pb2``)
   ``object_name``, ``filtered_object_name_prefix``, ``mesh_filename``, and one
   filter. See :doc:`/mesh_operations` for the filter parameters.

license
-------

Module ``flexiv.pdk.license.license_service_pb2``.

``ServiceLicense``
   ``service``, ``state`` (``LicenseState``), ``name``, ``display_name``,
   ``grpc_service``, ``detail``, ``expires`` (unset: never), ``license_id``.

``InstalledLicense``
   ``license_id``, ``customer``, ``issued``, ``expires``, ``services[]``,
   ``hardware_verified``, ``notes``.

``ListResponse``
   ``status``, ``services[]``, ``licenses[]``, ``tpm_available``,
   ``tpm_detail``, ``license_directory``, ``warnings[]``.

``SaveResponse``
   ``status``, ``services[]`` (state after install), ``newly_licensed[]``,
   ``file_path``.
