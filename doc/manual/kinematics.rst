Kinematics
==========

``KinematicsService`` (``client.kinematics``) computes forward and inverse
kinematics for a system in the scene. This guide follows
``examples/python/system_kinematics_example.py``.

Forward kinematics
------------------

``ComputeFK(FKRequest)`` returns the pose of a frame for given joint positions.

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - ``FKRequest`` field
     - Description
   * - ``system_name``
     - System to evaluate.
   * - ``target_frame_name``
     - Frame whose pose you want, e.g. ``"system_1.arm.flange"``.
   * - ``joint_positions``
     - Joint values (rad or m), one per actuated joint.

``FKResponse.pose`` is an ``SE3Pose``.

.. literalinclude:: /../../examples/python/system_kinematics_example.py
   :language: python
   :start-at: fk_req = FKRequest(
   :end-at: fk_pose = fk_res.pose
   :dedent: 12

Inverse kinematics
------------------

``ComputeIK(IKRequest)`` returns joint positions that place a frame at a pose,
avoiding collisions according to a collision configuration.

.. list-table::
   :header-rows: 1
   :widths: 30 12 58

   * - ``IKRequest`` field
     - Required
     - Description
   * - ``system_name``
     - yes
     - System to solve for.
   * - ``target_frame_name``
     - yes
     - A TCP, or an object attached to the system.
   * - ``target_pose``
     - yes
     - Desired pose of the target frame.
   * - ``collision_config_name``
     - yes
     - Name of a saved collision configuration (:doc:`collision`).
   * - ``null_space``
     - yes [#ns]_
     - Preferred redundancy: ``elbow_swivel_angle`` and external axis positions.
   * - ``joint_position_seed``
     - no
     - Initial guess at the solution.
   * - ``external_robot_axis``
     - no
     - ``EXTERNAL_ROBOT_NONE`` / ``_PRESET`` / ``_PREFERRED``.
   * - ``external_workpiece_axis``
     - no
     - ``EXTERNAL_WORKPIECE_NONE`` / ``_NOT_USED`` / ``_PRESET`` / ``_PREFERRED``.
   * - ``tool_symmetry``
     - no
     - Allow free rotation about the tool axis (for example, polishing wheels).

.. [#ns] Marked required in the ``.proto``. The example leaves it unset, which
   sends all-zero values.

``IKResponse.solution`` holds the joint positions; check ``status`` first.

.. literalinclude:: /../../examples/python/system_kinematics_example.py
   :language: python
   :start-at: print("Computing Inverse Kinematics for system_1.arm.flange with seed...")
   :end-before: if __name__ == "__main__":
   :dedent: 8

.. tip::

   A seed close to the expected solution makes IK faster and keeps the result
   on the same configuration branch. The example times both calls.

Complete example
----------------

The example prints ``grpc.RpcError`` instead of raising it and does not check
every ``status.code``. Production code should check both; see
:doc:`error_handling`.

.. literalinclude:: /../../examples/python/system_kinematics_example.py
   :language: python
