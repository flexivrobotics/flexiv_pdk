Math Conversions
================

The SDK includes helpers to convert between protobuf geometry messages and
NumPy (Python) or Eigen (C++).

Python: NumPy
-------------

.. code-block:: python

   from flexiv.pdk.spatial import to_numpy, to_proto

``to_numpy(message)``
   * ``Vector3`` → ``array([x, y, z])``
   * ``Quaternion`` → ``array([w, x, y, z])``; an unset (all-zero) quaternion
     is the identity here, but not necessarily on the server (see
     :doc:`/units_and_conventions`)
   * ``SE3Pose`` → 4×4 homogeneous matrix
   * ``JointWaypoint`` → ``(position, velocity)``, a pair of 1-D arrays
   * a ``repeated double`` field, list or tuple → 1-D ``float64`` array

``to_proto(value, target=None)``
   ``target`` names the message to make. A 1-D array needs it, because three
   numbers can be a position or three joints:

   * ``to_proto(T)`` or ``to_proto(T, SE3Pose)``, for a 4×4 homogeneous matrix
   * ``to_proto(r)`` or ``to_proto(r, Quaternion)``, for a
     ``scipy.spatial.transform.Rotation``
   * ``to_proto(p, Vector3)``, for ``[x, y, z]``
   * ``to_proto(q, Quaternion)``, for ``[w, x, y, z]``
   * ``to_proto((position, velocity), JointWaypoint)``, for a joint waypoint
   * ``to_proto(joints, list)``, for a ``repeated double`` field

   ``value`` can be anything ``np.asarray`` accepts. A 1-D array without a
   ``target`` raises ``TypeError``; the wrong shape for ``target`` raises
   ``ValueError``.

.. code-block:: python

   import numpy as np
   from scipy.spatial.transform import Rotation
   from flexiv.pdk.config_header_pb2 import ConfigHeader
   from flexiv.pdk.spatial import to_numpy, to_proto
   from flexiv.pdk.spatial.waypoint_pb2 import JointWaypoint

   T = np.eye(4)
   T[:3, :3] = Rotation.from_euler("z", 90, degrees=True).as_matrix()
   T[:3, 3] = [0.5, 0.0, 0.2]

   header = ConfigHeader(name="box_1", parent="world", pose_in_parent=to_proto(T))
   back = to_numpy(header.pose_in_parent)       # 4x4 matrix

   waypoint = to_proto((np.zeros(7), np.zeros(7)), JointWaypoint)
   position, velocity = to_numpy(waypoint)

``flexiv.pdk.physics`` converts an ``Inertia`` to and from its symmetric 3×3
tensor, reading only the upper triangle:

.. code-block:: python

   from flexiv.pdk import physics

   inertia = physics.to_proto(np.diag([0.1, 0.2, 0.3]))
   tensor = physics.to_numpy(inertia)                 # 3x3 matrix

``examples/python/numpy_conversion_example.py`` round-trips every one.

C++: Eigen
----------

``<flexiv/pdk/spatial/eigen_conversion.hpp>``, namespace ``flexiv::pdk::spatial``:

Every conversion is an overload of ``ToEigen`` or ``ToProto``, so the argument
type picks it:

.. code-block:: cpp

   Eigen::Vector3d                             ToEigen(const Vector3& v);
   Eigen::Quaterniond                          ToEigen(const Quaternion& q);  // all-zero (unset) is identity
   Eigen::Isometry3d                           ToEigen(const SE3Pose& p);
   Eigen::VectorXd                             ToEigen(const google::protobuf::RepeatedField<double>& v);
   std::pair<Eigen::VectorXd, Eigen::VectorXd> ToEigen(const JointWaypoint& waypoint);  // (position, velocity)

   Vector3                                     ToProto(const Eigen::Vector3d& v);
   Quaternion                                  ToProto(const Eigen::Quaterniond& q);
   SE3Pose                                     ToProto(const Eigen::Isometry3d& p);
   google::protobuf::RepeatedField<double>     ToProto(const Eigen::VectorXd& v);
   JointWaypoint                               ToProto(const Eigen::VectorXd& joint_position,
                                                       const Eigen::VectorXd& joint_velocity);

An Eigen expression converts by its size: ``ToProto(T.translation())`` gives a
``Vector3``, and ``ToProto(joints.head(3))`` of a ``VectorXd`` a repeated field.

``<flexiv/pdk/physics/eigen_conversion.hpp>``, namespace ``flexiv::pdk::physics``:

.. code-block:: cpp

   Eigen::Matrix3d ToEigen(const Inertia& I);
   Inertia         ToProto(const Eigen::Matrix3d& I);

``examples/cpp/src/eigen_conversion_example.cpp`` round-trips every one.
Example:

.. code-block:: cpp

   Eigen::VectorXd goal_joints_rad(7);
   goal_joints_rad << 0.0, -40.0 * kDegToRad, 0.0, 90.0 * kDegToRad, 0.0, 40.0 * kDegToRad, 0.0;
   *joint_waypoints->add_joint_waypoints()
       = flexiv::pdk::spatial::ToProto(goal_joints_rad, Eigen::VectorXd::Zero(7));

   const Eigen::Isometry3d tcp_pose = flexiv::pdk::spatial::ToEigen(cartesian_waypoint.pose());