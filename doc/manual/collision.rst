Collision Configurations
========================

Kinematics (IK) and point-to-point planning take the **name of a collision
configuration**. A collision configuration says which pairs of scene items may
touch and how much clearance to keep everywhere else.

.. code-block:: protobuf

   message CollisionConfig {
     string name = 1;                     // required
     repeated CollisionPair pairs = 2;    // allowed pairs, not checked
     double collision_margin = 3;         // minimum clearance (m), required
   }
   message CollisionPair { string name1 = 1; string name2 = 2; }

The server checks every pair of objects and system components except the ones
listed in ``pairs``. An empty ``pairs`` list checks every pair. Add a pair when
the two items are meant to touch, for example a gripper and the part it holds.

Pair names are objects or system components, for example ``box_1`` or
``system_1.arm``. Get the valid names from ``CollisionService.ListComponents``.

CollisionService
----------------

``client.collision`` stores collision configurations in the active workcell:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - RPC
     - Description
   * - ``Save``
     - ``SaveRequest(collision_config=...)``: create or overwrite.
   * - ``Get`` / ``Exists`` / ``Remove``
     - ``NameRequest(name)``.
   * - ``Rename``
     - ``RenameRequest(old_name, new_name)``.
   * - ``List``
     - ``Empty`` → ``names``.
   * - ``AddPair`` / ``RemovePair``
     - ``AddPairRequest(name, pair)`` / ``RemovePairRequest(name, pair)``: allow
       one more pair, or check it again, in an existing config.
   * - ``ListComponents``
     - ``Empty`` → every name valid in a pair.

Example
-------

The minimum, used by the kinematics example, is an empty configuration, which
checks every pair:

.. code-block:: python

   from flexiv.pdk.scene.collision.collision_config_pb2 import CollisionConfig, CollisionPair
   from flexiv.pdk.scene.collision.collision_service_pb2 import SaveRequest as CollisionSaveRequest

   client.collision.stub.Save(CollisionSaveRequest(
       collision_config=CollisionConfig(name="default_collision_config", collision_margin=0.0)))

With allowed pairs (``box_1`` is not checked against ``system_1.arm``):

.. literalinclude:: /../../examples/python/point_to_point_path_example.py
   :language: python
   :start-after: # 5. Collision configuration
   :end-before: # 6. Point-to-point path planning queries
   :dedent: 8

Discover valid names:

.. code-block:: python

   from google.protobuf.empty_pb2 import Empty
   print(list(client.collision.stub.ListComponents(Empty()).names))
