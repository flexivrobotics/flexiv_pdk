Robot Systems and Components
============================

A **system** is one robot arm plus everything attached to it. This guide covers
how a ``System`` is assembled, the component catalogue, custom tools, and
adding a system from a connected robot.

Anatomy of a system
-------------------

.. code-block:: text

   world
    └─ system base                          header: pose_in_parent in its parent
        └─ external_robot_axis (ExternalAxis, optional)   e.g. a linear rail
            └─ manipulator_adapter (Adapter, optional)
                └─ manipulator (Manipulator)            the arm, e.g. "arm"
                    └─ wrist_sensor (WristSensor, optional)
                        └─ tool_adapter (ToolAdapter, optional)
                            └─ tool[] (Tool, optional)
    └─ external_workpiece[] (ExternalWorkpiece, optional)  e.g. a rotary table

The header places the system base at ``pose_in_parent`` in its ``parent``. The
pose is converted to the world once, when the system is saved, so the system
does not follow its parent if the parent moves later. ``Get`` returns parent
``world`` and the pose in the world. The parent cannot be the system itself,
one of its links, or a frame attached to them.

.. list-table:: ``System`` fields
   :header-rows: 1
   :widths: 28 22 50

   * - Field
     - Type
     - Description
   * - ``header``
     - ``ConfigHeader``
     - **Required.** System name, parent and the pose of the system base in the parent.
   * - ``control_box_serial_number``
     - ``string``
     - **Required.** For example ``"CX01-01-T1-000001"``.
   * - ``manipulator``
     - ``Manipulator``
     - **Required.** ``name`` (unique in the system, e.g. ``"arm"``) and
       ``arm_serial_number``, the internal (engineering) serial number, e.g.
       ``"A02L-00-M3-000001"``. Optional
       ``lower_limit``/``upper_limit``/``home_position`` in rad.
   * - ``external_robot_axis``
     - ``ExternalAxis``
     - Axis the arm is mounted on (rail, pan-tilt platform, ...). Requires
       ``name``, ``manufacturer`` and ``model``. Optional ``home_position``
       (m or rad).
   * - ``manipulator_adapter``
     - ``Adapter``
     - Adapter on the external axis flange.
   * - ``wrist_sensor``
     - ``WristSensor``
     - Force/torque sensor. Requires ``name``, ``manufacturer`` and ``model``,
       e.g. ``manufacturer="flexiv"``, ``model="FT03-D1"``.
   * - ``tool_adapter``
     - ``ToolAdapter``
     - Catalogue adapter. Requires ``name``, ``manufacturer`` and ``model``.
       Optional ``rotation`` (rad).
   * - ``tool``
     - ``repeated Tool``
     - Catalogue or custom tools (``name``, ``manufacturer``, ``model``).
   * - ``external_workpiece``
     - ``repeated ExternalWorkpiece``
     - Actuated devices that move workpieces independently of the arm.

An ``Adapter`` is a rigid offset: ``xyz`` (m) and ``rpy`` (rad) give the pose of
the child base in the parent flange, with optional ``mass`` and ``inertia``.

.. literalinclude:: /../../examples/python/point_to_point_path_example.py
   :language: python
   :pyobject: create_system

Component catalogue
-------------------

``ComponentsService`` (``client.system_config``) lists the components the server
knows about. Each list call takes ``google.protobuf.Empty``:

* ``ListManipulators`` returns ``names``;
* ``ListToolAdapters``, ``ListTools``, ``ListCustomToolAdapters``,
  ``ListCustomTools``, ``ListExternalRobotAxes``, ``ListExternalWorkpieceAxes``
  return ``items`` of ``ManufacturerModel(manufacturer, model)``.

Use a listed ``manufacturer``/``model`` pair in ``Tool``, ``ToolAdapter`` or
``ExternalAxis``.

.. literalinclude:: /../../examples/python/components_service_example.py
   :language: python
   :start-after: # 5. List the available tool adapters
   :end-before: # 6. List the available tools
   :dedent: 8

Custom tools and adapters
~~~~~~~~~~~~~~~~~~~~~~~~~

Define your own end effector with ``CustomTool`` (``tcp`` pose relative to the
tool base, plus optional ``inertial``, ``collision`` and ``visual``) or
``CustomToolAdapter`` (one or more ``flange`` poses). Save it to the catalogue,
then reference it from a ``Tool`` by ``manufacturer`` and ``model``:

.. literalinclude:: /../../examples/python/components_service_example.py
   :language: python
   :start-after: # 3. Create a custom tool
   :end-before: # 4. Create a custom tool adapter
   :dedent: 8

.. literalinclude:: /../../examples/python/components_service_example.py
   :language: python
   :start-after: # 10. Add a robot system to the scene with the custom tool from step 3
   :end-before: # 11. Get the system urdf
   :dedent: 8

``RemoveCustomTool`` and ``RemoveCustomToolAdapter`` take a ``ManufacturerModel``.

Adding a system from a real robot
---------------------------------

``SystemService.AddConnectedSystem`` connects to a physical robot (through RDK)
by serial number, reads its configuration, and saves it as a system in the
active workcell. Afterwards, read it back with ``ConfigService.Get``.

.. literalinclude:: /../../examples/python/system_setup_from_rdk_example.py
   :language: python
   :start-after: # 3. Add a robot system to the scene
   :end-before: if __name__ == "__main__":
   :dedent: 8

Requirements: the robot is reachable and RDK remote mode is enabled. Change the
serial number to your robot's. ``AddConnectedSystem`` takes the robot's public
serial number (as used by RDK, e.g. ``"Rizon4-062065"``), not the internal
``arm_serial_number`` stored in ``Manipulator``.

To reposition a connected system, ``Get`` it, edit ``header.pose_in_parent``,
and ``Save`` it again:

.. literalinclude:: /../../examples/python/camera_example.py
   :language: python
   :start-after: # 3. Set the pose of the robot system in the scene
   :end-before: # 4. Add a camera to the scene
   :dedent: 8

Other system queries
--------------------

``SystemService`` (``client.system``):

``GetUrdf(GetUrdfRequest(name))``
   URDF of one system.
``GetArmSerialNumber(GetArmSerialNumberRequest(system_name))``
   ``arm_serial_number`` and ``arm_public_serial_number``.
``GetCalibrationStatus(GetCalibrationStatusRequest(system_name))``
   ``calibrated`` is true when a calibration exists and was applied.

Default versus current joint position
-------------------------------------

A system in the scene has two joint vectors. Neither is the real robot's
position; moving a real or simulated robot is done with the Flexiv RDK.

* **Default** joint position: ``Manipulator.home_position`` (rad) and
  ``ExternalAxis.home_position`` (m or rad) in the saved ``System``. Change it
  by editing the system and saving it with ``ConfigService.Save``.
* **Current** joint position: ``StateService.GetJointPosition`` /
  ``SetJointPosition`` (``client.system_state``). The joint positions the
  system has in the scene right now, used by planning, collision checks and
  the system's frames. A system starts at its default position when it is
  added or its configuration changes. ``SetJointPosition`` takes effect
  immediately and is not saved.

``GetJointPositionRequest`` and ``SetJointPositionRequest`` take
``system_name`` and an optional ``joint_group``: ``JOINT_GROUP_SYSTEM`` (the
default, all actuated joints), ``JOINT_GROUP_ARM``,
``JOINT_GROUP_EXTERNAL_ROBOT_AXIS`` or ``JOINT_GROUP_EXTERNAL_WORKPIECE_AXIS``.
``SetJointPositionRequest.joint_position`` has one value per joint in the group.

.. code-block:: python

   from flexiv.pdk.system.state_service_pb2 import SetJointPositionRequest
   from flexiv.pdk.system.components.joint_group_pb2 import JointGroup

   res = client.system_state.stub.SetJointPosition(SetJointPositionRequest(
       system_name="system_1",
       joint_group=JointGroup.JOINT_GROUP_ARM,
       joint_position=[0.0, -0.7, 0.0, 1.57, 0.0, 0.7, 0.0],
   ))
   if res.status.code != 0:
       raise RuntimeError(res.status.message)
