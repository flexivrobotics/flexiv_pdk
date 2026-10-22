Units and Conventions
=====================

Units
-----

All values are SI unless stated otherwise.

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Quantity
     - Unit
   * - Position, length, size, distance
     - metre (m)
   * - Angle, joint position of a revolute joint
     - radian (rad)
   * - Joint position of a prismatic joint (linear rail)
     - metre (m)
   * - Joint velocity
     - rad/s or m/s
   * - Force / torque (``Wrench``)
     - newton (N) / newton-metre (Nm)
   * - Mass
     - kilogram (kg)
   * - Inertia
     - kg·m²
   * - Area (mesh filters)
     - m²

Rotations
---------

Orientations are unit quaternions:

.. code-block:: protobuf

   message Quaternion { double x = 1; double y = 2; double z = 3; double w = 4; }

.. warning::

   **An unset quaternion is all zeros.** The SDK conversion helpers
   (:doc:`/math_conversions`) read it as the identity, but the server does not
   guarantee the same. When you build a ``Quaternion`` by hand, always set
   ``w=1.0`` for "no rotation". This also applies to the ``origin`` of
   ``Visual`` and ``Collision`` and to ``PathRefinement.rotation_offset``.

Normalize quaternions before sending them.

Some component messages (``Adapter``) use ``xyz`` plus ``rpy`` (roll, pitch,
yaw in radians) instead of a quaternion.

Element order in the helpers
----------------------------

The protobuf ``Quaternion`` stores ``x, y, z, w``. The conversion helpers follow
their libraries' conventions:

* Python ``to_numpy(Quaternion)`` returns ``[w, x, y, z]``, and
  ``to_proto(array, Quaternion)`` reads ``[w, x, y, z]``.
* C++ ``ToEigen``/``ToProto`` use ``Eigen::Quaterniond``, which has named
  accessors, so there is no ordering ambiguity.

See :doc:`/math_conversions`.

Poses
-----

``SE3Pose`` is a position and a rotation. A pose is always relative to some
frame:

* ``ConfigHeader.pose_in_parent`` is relative to ``ConfigHeader.parent``.
* ``Frame`` carries both ``pose_world`` and ``pose_parent``.
* Points in path generator requests are in the **parent object's frame** unless
  the field documentation says *world frame* (for example
  ``MeshRasterPath.specified_direction``).

Joint vectors
-------------

Joint vectors are plain ``repeated double`` lists. For a 7-DoF Rizon arm they
hold seven values ordered from base to flange. With external axes, the
``JOINT_GROUP_SYSTEM`` group contains all actuated joints of the system;
``JOINT_GROUP_ARM``, ``JOINT_GROUP_EXTERNAL_ROBOT_AXIS`` and
``JOINT_GROUP_EXTERNAL_WORKPIECE_AXIS`` select a subset.

Proto3 defaults
---------------

Fields you do not set take their proto3 default: ``0``, ``""``, ``false``, the
first enum value, or an empty message. Some proto comments describe a
different "default" (for example a boolean documented as "default true"). The
server may treat zero values as "use the default", but do not rely on it: set
every field you care about explicitly.
