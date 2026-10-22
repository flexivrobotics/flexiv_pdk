The Scene Model
===============

The scene is a tree of named **frames** rooted at ``world``. Persistent scene
items, called **configs**, each own one or more frames.

Configs
-------

A config is a saved, named item in the active workcell. ``ConfigService``
(``client.config``) stores and retrieves all of them through one set of RPCs;
the ``ConfigType`` enum selects the kind:

.. list-table::
   :header-rows: 1
   :widths: 32 30 38

   * - ``ConfigType``
     - Message
     - ``SaveConfigRequest`` / ``GetConfigResponse`` field
   * - ``CONFIG_TYPE_OBJECT``
     - ``scene.Object``
     - ``object``
   * - ``CONFIG_TYPE_SYSTEM``
     - ``system.System``
     - ``system``
   * - ``CONFIG_TYPE_CAMERA``
     - ``scene.Camera``
     - ``camera``
   * - ``CONFIG_TYPE_COORDINATE``
     - ``scene.Coordinate``
     - ``coordinate``
   * - ``CONFIG_TYPE_SYSTEM_POSE``
     - ``scene.TargetWaypoint``
     - ``system_pose``
   * - ``CONFIG_TYPE_OBJECT_POSE``
     - ``scene.Coordinate``
     - ``object_pose``
   * - ``CONFIG_TYPE_GRASP_POSE``
     - ``scene.Coordinate``
     - ``grasp_pose``
   * - ``CONFIG_TYPE_SURFACE_PATH``
     - ``surface_finish.Path``
     - ``surface_path``
   * - ``CONFIG_TYPE_P2P_PATH``
     - ``point_to_point_path.Path``
     - ``p2p_path``
   * - ``CONFIG_TYPE_ALL``
     - (search all types; slower)
     -

``ConfigService`` RPCs:

* ``Save(SaveConfigRequest)``: create or overwrite. Set exactly one field of the
  ``config`` oneof.
* ``Get``, ``Exists``, ``Remove`` take ``TypeNameConfigRequest(type, name)``.
* ``List(ListConfigRequest(type))`` returns ``names``.
* ``Rename(RenameConfigRequest(type, old_name, new_name))``.
* ``GetParent``/``SetParent`` and ``GetPose``/``SetPose`` edit the header
  fields without re-sending the whole config. ``SetParent`` keeps the saved
  pose relative to the new parent, so the item moves with it (unlike
  ``FrameService.SetParent``, see `Re-parenting`_).
* ``HasParent(HasParentRequest(type, name, parent_name))`` and
  ``HasChild(HasChildRequest(type, name, child_name))`` test tree relations.
  Here ``type`` is a ``FrameType``, not a ``ConfigType``.
* ``GetUrdf(Empty)`` returns a URDF of everything in the scene.

The config header
-----------------

Almost every config starts with a ``ConfigHeader``:

.. code-block:: protobuf

   message ConfigHeader {
     string name = 1;                     // unique name, required
     string parent = 2;                   // parent frame name, e.g. "world"
     spatial.SE3Pose pose_in_parent = 3;  // pose relative to the parent
   }

A small helper keeps code short (the examples use the same one):

.. literalinclude:: /../../examples/python/mesh_filter_example.py
   :language: python
   :pyobject: make_header

Frames
------

Saving a config creates frames in the server's transform tree. ``FrameService``
(``client.frame``) reads and moves them. Frames are addressed by a
``FrameType`` and a name. Changes made through ``FrameService`` take effect
immediately but are not saved; reloading the workcell restores the parents and
poses saved in ``ConfigService``.

``FrameService`` RPCs:

* ``Exists``, ``Get`` (returns a ``Frame``), ``Remove`` take ``(type, name)``.
* ``List(ListFramesRequest(type))`` returns ``names``.
* ``Rename(RenameFrameRequest(type, old_name, new_name))``.
* ``GetParent(GetFrameParentRequest(type, name))`` returns ``parent_name``;
  ``SetParent`` is described in `Re-parenting`_.
* ``GetPose``/``UpdatePose``, see `Reference frames`_.
* ``HasParent(HasFrameParentRequest(type, name, parent_name))`` and
  ``HasChild(HasFrameChildRequest(type, name, child_name))``.

Frame names are hierarchical. A robot system ``system_1`` with a manipulator
named ``arm`` produces frames such as:

* ``system_1``: the system root (``FRAME_TYPE_SYSTEM_ROOT``)
* ``system_1.arm``: the manipulator, used in collision pairs
* ``system_1.arm.flange``: the flange, used as a TCP for kinematics and planning
  (``FRAME_TYPE_TCP``)

Use any of these as a ``parent`` to attach items to the robot. For example, a
wrist camera uses ``parent="system_1.arm.flange"``.

Frame types: ``CAMERA``, ``COORDINATE``, ``SURFACE_PATH_ROOT``,
``SURFACE_PATH_WAYPOINT``, ``OBJECT``, ``OBJECT_PATTERN_ROOT``,
``OBJECT_PATTERN_INSTANCE``, ``P2P_PATH_ROOT``, ``P2P_PATH_WAYPOINT``,
``SYSTEM_ROOT``, ``SYSTEM_LINK``, ``TCP``, ``GRASP_POSE``, ``OBJECT_POSE``,
``SYSTEM_POSE`` (all prefixed ``FRAME_TYPE_``).

Reference frames
~~~~~~~~~~~~~~~~

``FrameService.GetPose`` and ``UpdatePose`` take a ``ReferenceFrame``:

* ``REFERENCE_FRAME_WORLD``: pose relative to ``world``;
* ``REFERENCE_FRAME_PARENT``: pose relative to the frame's parent;
* ``REFERENCE_FRAME_NAMED``: pose relative to the frame named in
  ``reference_name`` (required in this case).

.. code-block:: python

   from flexiv.pdk.frame_service_pb2 import GetFramePoseRequest
   from flexiv.pdk.spatial.frame_defs_pb2 import FrameType, ReferenceFrame

   res = client.frame.stub.GetPose(GetFramePoseRequest(
       type=FrameType.FRAME_TYPE_TCP,
       name="system_1.arm.flange",
       reference=ReferenceFrame.REFERENCE_FRAME_WORLD,
   ))
   print(res.pose)

Re-parenting
~~~~~~~~~~~~

``FrameService.SetParent(SetFrameParentRequest(type, name, parent_name,
policy))`` takes a ``ParentingPolicy``:

``PARENTING_PRESERVE_WORLD`` (default)
   The frame stays where it is in the world; its local pose is recomputed.
``PARENTING_PRESERVE_LOCAL``
   The local pose is kept, so the frame moves in the world, and its children
   move with it.
``PARENTING_PRESERVE_LOCAL_FIX_CHILDREN``
   The local pose is kept and the frame moves, but its children keep their
   world poses.

Config pose versus frame pose
-----------------------------

``ConfigService.SetPose`` changes the **saved** config and emits a scene event
with origin ``ORIGIN_CONFIG``. ``FrameService.UpdatePose`` moves the frame in the
transform layer only (for example, while dragging in a GUI) and emits
``ORIGIN_FRAME``. Save the config to make a frame change permanent. See
:doc:`/scene_events`.
