What Is Flexiv PDK?
===================

Flexiv PDK (Planning Development Kit) is a client SDK for building robotic
applications on top of a running PDK server.

What the PDK provides
---------------------

The Flexiv PDK provides four groups of functionality:

1. **Scene setup.** Build a *workcell* containing robot systems, objects,
   cameras and named coordinate frames, and query or move anything in it.
2. **Surface finish.** Create a tool path on an object (from CAD edges or faces,
   or from a mesh) and compute the robot motion that follows it.
3. **Point-to-point motion.** Plan collision-free robot motion between joint
   configurations or saved target poses, optionally carrying a grasped object.
4. **Perception.** Capture camera images and point clouds, reconstruct the
   scene, and process meshes.

Python and C++ both provide all four.

Architecture
------------

.. code-block:: text

   ┌──────────────────────────┐          gRPC (HTTP/2)         ┌──────────────────────┐
   │  Your application         │  ───────────────────────────▶  │  PDK server           │
   │                           │                                │                       │
   │  Python  flexiv.pdk       │   requests / responses         │  workcells, scene,    │
   │  C++     flexiv::pdk      │  ◀───────────────────────────  │  kinematics, planning,│
   │  CLI     pdk-scene        │   server-streamed events       │  perception, licensing│
   └──────────────────────────┘                                └──────────┬───────────┘
                                                                          │ RDK
                                                                          ▼
                                                                  Flexiv robots, cameras

* The **server** owns all state: the active workcell, the scene, saved paths and
  licenses. It listens on ``localhost:50052`` by default.
* The **client SDK** is thin. It opens one gRPC channel and gives you a *stub*
  for each service. Requests and responses are Protocol Buffers messages
  generated from the ``.proto`` files in ``proto/flexiv/pdk/``.
* Helpers are layered on top: conversions to NumPy, Eigen and Three.js, a reconnecting
  subscriber for streamed scene events, and license-file handling.

Where to go next
----------------

* :doc:`install_for_python` or :doc:`install_for_cpp` to install the SDK.
* :doc:`build_your_first_scene` to connect and build a first scene.
* :doc:`/api_overview` to understand how the client is organized.
