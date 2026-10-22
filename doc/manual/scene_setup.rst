Setting Up a Scene
==================

This guide builds a scene with objects and robot systems. It follows
``examples/python/scene_example.py`` (and its C++ twin
``examples/cpp/src/scene_example.cpp``).

Prerequisite: an active workcell (:doc:`/workcells`).

Objects
-------

An ``Object`` (``flexiv.pdk.scene.object_pb2``) is a rigid body in the scene.

.. list-table::
   :header-rows: 1
   :widths: 22 22 56

   * - Field
     - Type
     - Description
   * - ``header``
     - ``ConfigHeader``
     - **Required.** Name, parent and pose.
   * - ``visual``
     - ``repeated Visual``
     - What the object looks like. Use CAD (``.stp``, ``.step``) for precise
       tool-path generation, or a mesh (``.dae``, ``.obj``, ``.stl``) for scanned
       parts.
   * - ``collision``
     - ``repeated Collision``
     - Geometry used for collision checking. Empty means the object never
       collides.
   * - ``inertial``
     - ``physics.Inertial``
     - Mass, centre of mass and inertia (optional).
   * - ``reference_only``
     - ``bool``
     - Keep as a template for patterns or feeders; do not add to the scene.

``Visual`` and ``Collision`` each have an ``origin`` (``SE3Pose`` relative to
the object) and a ``Shape``, which is one of ``box``, ``sphere``, ``cylinder``,
``capsule``, ``mesh``, ``convex_mesh`` or ``octomap``.

The simplest object has only a header (it becomes a bare frame):

.. literalinclude:: /../../examples/python/scene_example.py
   :language: python
   :start-after: # Object 1
   :end-before: # Object 2
   :dedent: 8

Primitive shapes
~~~~~~~~~~~~~~~~

.. literalinclude:: /../../examples/python/point_to_point_path_example.py
   :language: python
   :pyobject: make_box

Mesh and CAD files
~~~~~~~~~~~~~~~~~~

``Mesh.filename`` is a path **on the server machine**. The server must be able
to read it; with a containerized server, put files under the server's
``user_data`` folder and use the path as the server sees it. ``Mesh.scale`` is
required: use ``(1, 1, 1)`` for no scaling.

.. literalinclude:: /../../examples/python/mesh_filter_example.py
   :language: python
   :pyobject: make_mesh_visual

The examples use a 1 m × 1 m plane mesh shipped in
``examples/assets/plane_1m_10x10.obj``.

Robot systems
-------------

A ``System`` (``flexiv.pdk.system.system_pb2``) describes one robot and
everything mounted on it. The minimum is a header, the control box serial
number and a manipulator:

.. literalinclude:: /../../examples/python/scene_example.py
   :language: python
   :start-after: # System 1: Placed at x=-0.7
   :end-before: try:
   :dedent: 8

The second system in the example is rotated 180° about Z with the quaternion
``(x, y, z, w) = (0, 0, 1, 0)`` so that the two robots face each other.

See :doc:`systems_and_components` for mounts, tools, external axes, and adding
a system by connecting to a real robot.

Cameras
-------

A ``Camera`` places a camera frame and its view frustum in the scene:

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Field
     - Description
   * - ``header``
     - Pose of the camera. Parent to ``world`` for a fixed camera or to a robot
       link (such as ``system_1.arm.flange``) for a wrist camera.
   * - ``far_width``, ``far_height``
     - Size of the far plane of the frustum (m).
   * - ``far_distance``, ``near_distance``
     - Far and near clipping distances (m).
   * - ``depth_scale``
     - ``depth [m] = depth [raw] / depth_scale`` (e.g. ``1000`` for millimetres).
   * - ``camera_id``
     - Device ID of the physical camera.

.. literalinclude:: /../../examples/python/camera_example.py
   :language: python
   :start-after: # 4. Add a camera to the scene
   :end-before: try:
   :dedent: 8

Capturing images is covered in :doc:`cameras_and_reconstruction`.

Coordinates
-----------

A ``Coordinate`` is a named frame, like a URDF link without geometry, useful for
fixtures and reference points. ``scale`` is the display size of the axes.
The same message type is used for saved object poses (``object_pose``) and grasp
poses (``grasp_pose``).

.. code-block:: python

   from flexiv.pdk.config_service_pb2 import SaveConfigRequest
   from flexiv.pdk.scene.coordinate_pb2 import Coordinate

   # make_header() is the helper shown in "The Scene Model"
   fixture = Coordinate(header=make_header("fixture", px=0.4, pz=0.1))
   client.config.stub.Save(SaveConfigRequest(coordinate=fixture))

Inspecting and editing the scene
--------------------------------

.. code-block:: python

   from google.protobuf.empty_pb2 import Empty
   from flexiv.pdk.config_service_pb2 import (
       ConfigType, ListConfigRequest, SetPoseRequest, TypeNameConfigRequest)
   from flexiv.pdk.spatial.geometry_pb2 import Quaternion, SE3Pose, Vector3

   # List all objects
   print(client.config.stub.List(ListConfigRequest(type=ConfigType.CONFIG_TYPE_OBJECT)).names)

   # Move an object (persisted)
   client.config.stub.SetPose(SetPoseRequest(
       type=ConfigType.CONFIG_TYPE_OBJECT, name="box_1",
       pose=SE3Pose(position=Vector3(x=0.6), rotation=Quaternion(w=1.0))))

   # Remove it
   client.config.stub.Remove(TypeNameConfigRequest(type=ConfigType.CONFIG_TYPE_OBJECT, name="box_1"))

   # Export the whole scene as URDF
   print(client.config.stub.GetUrdf(Empty()).urdf_content)

The ``pdk-scene`` CLI does the same from a shell; see :doc:`/pdk_scene_cli`.

Complete example
----------------

.. note::

   The examples catch ``grpc.RpcError`` and print it, and they do not check
   every ``status.code``. Production code should check both; see
   :doc:`error_handling`.

Python:

.. literalinclude:: /../../examples/python/scene_example.py
   :language: python

C++:

.. literalinclude:: /../../examples/cpp/src/scene_example.cpp
   :language: cpp
