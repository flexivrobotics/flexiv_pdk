Point-to-Point Motion Planning
==============================

``PointToPointPathService.Plan`` (``client.point_to_point_path``) plans a
collision-free motion through a sequence of goals and **saves the result as a
config** of type ``CONFIG_TYPE_P2P_PATH``. Read it back with
``ConfigService.Get``.

.. note:: ``PointToPointPathService`` requires the ``point_to_point_path`` license
   (:doc:`/activate_licenses`).

Request
-------

.. list-table:: ``PointToPointPathRequest``
   :header-rows: 1
   :widths: 30 70

   * - Field
     - Description
   * - ``path_name``
     - **Required.** Name under which the planned path is saved.
   * - ``collision_config_name``
     - **Required.** A saved collision configuration (:doc:`collision`).
   * - ``joint_waypoints``
     - *One of.* ``PTPJointWaypoints``: ``system_name``, ``tcp_name`` (used to
       compute Cartesian poses) and a list of ``JointWaypoint``.
   * - ``target_waypoints``
     - *One of.* ``PTPTargetWaypoints``: names of saved system poses
       (``TargetWaypoint`` configs).

Result
------

``point_to_point_path.Path`` (output only):

* ``header``: the path name;
* ``system_name``, ``tcp_name``, ``collision_config_name``;
* ``cartesian_waypoints``: TCP poses of the goals (always present);
* ``joint_waypoints``: the planned joint trajectory (present when planning
  succeeded);
* ``tcp_to_attach_object``, ``object_grasp_pose``: used when carrying an object.

Planning between joint configurations
-------------------------------------

From ``examples/python/point_to_point_path_example.py``:

.. literalinclude:: /../../examples/python/point_to_point_path_example.py
   :language: python
   :start-after: # 6. Point-to-point path planning queries
   :end-before: # Helper for joint waypoints
   :dedent: 8

.. literalinclude:: /../../examples/python/point_to_point_path_example.py
   :language: python
   :start-after: # Helper for joint waypoints
   :end-before: # 2. With collision
   :dedent: 8

The example prints ``grpc.RpcError`` instead of raising it. Production code
should check both layers; see :doc:`error_handling`.

Attach an object to the flange (by parenting it to ``system_1.arm.flange``) and
it moves with the robot and is collision-checked along the path. The example
does this with ``box_4``.

Planning between saved system poses
-----------------------------------

A **system pose** (``scene.TargetWaypoint``) stores a TCP name together with a
Cartesian pose and the joint configuration that reaches it. Save poses once,
then plan between them by name. From ``examples/python/system_pose_example.py``:

.. literalinclude:: /../../examples/python/system_pose_example.py
   :language: python
   :start-after: # 5. Add a system pose object to the scene, attached to system_1
   :end-before: # 6. Get the system pose object back
   :dedent: 8

.. literalinclude:: /../../examples/python/system_pose_example.py
   :language: python
   :start-after: # 10. Run a point-to-point path plan directly from the retrieved system pose target waypoints
   :end-before: if __name__ == "__main__":
   :dedent: 8

C++
---

``examples/cpp/src/point_to_point_path_example.cpp`` does the same in C++
(``kDegToRad`` is defined in the example as ``π / 180``):

.. literalinclude:: /../../examples/cpp/src/point_to_point_path_example.cpp
   :language: cpp
   :start-after: // 6. Point-to-point path planning queries
   :end-before: std::cout << "All scene setup and planning queries complete."
   :dedent: 2

``RunPlan`` fills the joint waypoints, calls ``Plan`` and reads the saved path
back:

.. literalinclude:: /../../examples/cpp/src/point_to_point_path_example.cpp
   :language: cpp
   :start-at: void RunPlan(
   :end-before: } // namespace

The ROS 2 package in ``examples/ros`` builds the same source:

.. code-block:: bash

   PDK_SERVER_ADDR=192.168.1.100:50052 ros2 run pdk_cpp_examples point_to_point_path_example
