Surface Finish: Tool Paths and Robot Motion
===========================================

``SurfaceFinishService`` (``client.surface_finish``) builds a tool path on an
object and turns it into robot motion, for sanding, polishing, painting,
dispensing and similar tasks. It works in **stages**. Data from every stage is
kept and can be read, and **redoing a stage clears the results of later
stages**.

.. note:: ``SurfaceFinishService`` requires the ``surface_finish`` license
   (:doc:`/activate_licenses`).

.. code-block:: text

   Stage 1                    Stage 2                  Stage 3                       Export
   GenerateNominalPath  ──▶  RefinePath  ──────────▶  CreateRobotMotion  ──────▶  GenerateRCATrajectoryFile
   nominal_cartesian          refined_cartesian        basic_solution /
                                                       advanced_solution

The result is a ``surface_finish.Path`` config (type ``CONFIG_TYPE_SURFACE_PATH``)
parented to the object. Read it with ``SurfaceFinishService.Get`` or
``ConfigService.Get``.

Stage 1: nominal path
---------------------

``GenerateNominalPath(GenerateNominalPathRequest)`` takes a ``header`` (the
path name, with ``parent`` set to the **object** the path lies on) and one path
generator. It returns ``path_names``: one request can create several paths,
for example a raster split into separate passes.

.. list-table:: Path generators
   :header-rows: 1
   :widths: 26 16 58

   * - Request field
     - Source
     - Description
   * - ``manual_path``
     - any
     - ``ManualPath``: you provide ``CartesianWaypoint`` s, relative to the parent.
   * - ``mesh_sketch_path``
     - mesh
     - ``MeshSketchPath``: a polyline through ``points`` on the mesh surface
       (parent frame), resampled at ``fixed_spacing`` or ``variable_spacing``.
   * - ``mesh_raster_path``
     - mesh
     - ``MeshRasterPath``: a raster (zig-zag) pattern covering the mesh or a
       ``polygon_border`` region.
   * - ``edge_path``
     - CAD
     - ``EdgePath``: follows CAD edges; adjacent ``faces`` define the tool Z axis.
   * - ``surface_scan_path``
     - CAD
     - ``FaceRasterPath``: a raster pattern on CAD faces.
   * - ``surface_sketch_path``
     - CAD
     - ``FaceSketchPath``: a path through sketch ``points`` on CAD faces.

Mesh sketch path
~~~~~~~~~~~~~~~~

.. literalinclude:: /../../examples/python/mesh_toolpath_sketch_example.py
   :language: python
   :start-at: path_req = GenerateNominalPathRequest(
   :end-before: except grpc.RpcError
   :dedent: 12

Mesh raster path
~~~~~~~~~~~~~~~~

.. literalinclude:: /../../examples/python/mesh_toolpath_raster_example.py
   :language: python
   :start-at: path_req = GenerateNominalPathRequest(
   :end-before: except grpc.RpcError
   :dedent: 12

Key ``MeshRasterPath`` parameters (all lengths in m, angles in rad):

``raster_line_spacing``
   Distance between raster lines.
``fixed_spacing``
   Distance between waypoints along a line.
``blending_radius``
   Corner blending radius.
``border_offset``
   Inward offset from the region border.
``raster_path_joining_distance_threshold``
   Lines closer than this are joined into one continuous path.
``principal_rotation_angle`` *or* ``specified_direction``
   Raster direction: an angle about the mesh's principal direction, or a
   world-frame vector projected onto the mesh.
``minimum_toolpath_length``
   Shorter paths after splitting are dropped.
``align_with_initial_direction`` / ``align_with_previous`` / ``align_with_direction``
   How each waypoint's X axis is oriented.

CAD-based generators
~~~~~~~~~~~~~~~~~~~~

``EdgePath``, ``FaceRasterPath`` and ``FaceSketchPath`` follow the CAD edges or
faces listed in ``edges`` or ``faces``. Each entry is the OCCT entry string
(``TDF_Label``) of a ``TopoDS_Edge`` or ``TopoDS_Face`` in the STEP file. In
C++, ``flexiv::pdk::surface_finish::ToOcctEntryString(shape, shape_tool)``
(``<flexiv/pdk/surface_finish/occt_entry_string.hpp>``) computes it. The helper
exists only in builds with ``FLEXIV_PDK_ENABLE_OCCT_INTEGRATION=ON``, and the
binary release ships its header only when the library contains it.

The object must have a ``Visual`` whose ``mesh.filename`` is the STEP file. If an
object has several visual files, set ``cad_filename`` (or ``mesh_filename``) to
choose one.

Waypoint spacing for CAD paths (and for ``MeshSketchPath``) is either
``fixed_spacing`` (m) or ``variable_spacing``, a ``VariableSpacing`` (``min_spacing``, ``max_spacing``, ``position_tolerance``,
``orientation_tolerance``). ``FaceRasterPath`` can be bounded by an
``EdgeBorder`` (keep a distance from given edges) or a ``PolygonBorder``.

Stage 2: refinement
-------------------

Optional. ``RefinePath(RefinePathRequest(path_name, refinement))`` modifies
the nominal waypoints. Stage 3 uses ``refined_cartesian`` if it is present,
otherwise ``nominal_cartesian``. ``PathRefinement`` operations are applied in this order:

1. ``reversed_order``: reverse the waypoint order;
2. ``align_with_previous``: rotate each waypoint about its local Z to align with
   the previous one;
3. ``rotation_offset``: rotate each waypoint in its own frame;
4. ``position_offset``: translate each waypoint in its own frame.

.. warning:: Set ``rotation_offset`` to the identity (``w=1``) if you do not want
   a rotation. An unset quaternion is all zeros.

Stage 3: robot motion
---------------------

``CreateRobotMotion(CreateRobotMotionRequest(path_name, solver_preferences))``
computes joint trajectories.

.. list-table:: ``SolverPreferences``
   :header-rows: 1
   :widths: 30 70

   * - Field
     - Description
   * - ``system_name``
     - **Required.** The system that executes the path.
   * - ``tcp_ecp_name``
     - **Required.** The TCP (tool) or ECP (external control point) that follows
       the path, e.g. ``"system_1.arm.flange"``.
   * - ``solver_type``
     - ``SOLVER_TYPE_BASIC`` (result in ``basic_solution``) or
       ``SOLVER_TYPE_ADVANCED`` (result in ``advanced_solution``).
   * - ``null_space``
     - Desired elbow swivel angle and external axis positions.
   * - ``external_robot_axis``, ``external_workpiece_axis``
     - How external axes may move (none, preset, preferred, not used).
   * - ``tool_symmetry``
     - Ignore rotation about the tool axis (for example, polishing wheels).
   * - ``joint_position_seed``
     - Start configuration. If empty, the current robot state is used.
   * - ``tcp_to_attach_object``, ``object_grasp_pose``
     - ECP only: the robot holds the part and moves it past a fixed tool.

.. literalinclude:: /../../examples/python/linear_path_trajectory_generation_example.py
   :language: python
   :start-after: # 5. Run Basic solve to compute the robot joint positions for the generated path
   :end-before: # 6. Get the generated path config
   :dedent: 8

Process parameters and export
-----------------------------

Each ``CartesianWaypoint`` carries ``velocity``, ``acceleration`` and a
``wrench`` (force/torque to apply in contact). Edit them on the path and save
it back with ``ConfigService.Save(SaveConfigRequest(surface_path=...))``. Then
``GenerateRCATrajectoryFile`` writes a robot trajectory (``.traj``) file on the
server, at ``<workcell>/linear_path/<path_name>/<path_name>.traj``, where
``<workcell>`` is the active workcell's folder in the server's workcell
directory (``flexiv_pdk_data/workcell/`` for the containerized server, see
:doc:`install_server`).

.. literalinclude:: /../../examples/python/linear_path_trajectory_generation_example.py
   :language: python
   :start-after: # 6. Get the generated path config and set the Cartesian
   :end-before: if __name__ == "__main__":
   :dedent: 8

Complete example
----------------

The example prints ``grpc.RpcError`` instead of raising it and does not check
every ``status.code``. Production code should check both; see
:doc:`error_handling`.

.. literalinclude:: /../../examples/python/linear_path_trajectory_generation_example.py
   :language: python
