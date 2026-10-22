Verify with Example Programs
============================

The `PDK repository <https://github.com/flexivrobotics/flexiv_pdk>`_ ships
runnable examples in ``examples/``. Clone it; paths on this page are relative to
its root:

.. code-block:: bash

   git clone https://github.com/flexivrobotics/flexiv_pdk.git
   cd flexiv_pdk

Every example except ``watch_scene_events_example.py`` creates a workcell called
``example_workcell``, and most delete it first, so **do not run them against a
workcell you want to keep**.

Python examples
---------------

Run from the repository root with the SDK installed and a server running:

.. code-block:: bash

   python examples/python/scene_example.py

The Python examples connect to ``localhost:50052``. Set ``PDK_SERVER_ADDR`` to
use another server:

.. code-block:: bash

   PDK_SERVER_ADDR="192.168.1.100:50052" python examples/python/scene_example.py

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Script
     - Shows
     - Needs
   * - ``scene_example.py``
     - Workcell, three objects, two facing robot systems.
       :doc:`/scene_setup`
     - server
   * - ``system_kinematics_example.py``
     - Forward and inverse kinematics, with and without a seed.
       :doc:`/kinematics`
     - server
   * - ``components_service_example.py``
     - Custom tools and adapters, component catalogue, system URDF.
       :doc:`/systems_and_components`
     - server
   * - ``system_setup_from_rdk_example.py``
     - Add a system from a connected robot.
       :doc:`/systems_and_components`
     - real robot (RDK)
   * - ``point_to_point_path_example.py``
     - P2P planning with several collision configurations.
       :doc:`/point_to_point_path`
     - P2P license
   * - ``system_pose_example.py``
     - Save system poses from FK; plan between them by name.
       :doc:`/point_to_point_path`
     - P2P license
   * - ``mesh_toolpath_sketch_example.py``
     - Sketch tool path on a mesh. :doc:`/surface_finish`
     - surface-finish license, mesh asset
   * - ``mesh_toolpath_raster_example.py``
     - Raster tool path on a mesh. :doc:`/surface_finish`
     - surface-finish license, mesh asset
   * - ``linear_path_trajectory_generation_example.py``
     - Full pipeline: path, robot motion, process parameters, ``.traj`` export.
       :doc:`/surface_finish`
     - surface-finish license, mesh asset
   * - ``mesh_area_extraction_example.py``
     - Cut a polygon out of a mesh. :doc:`/mesh_operations`
     - mesh-operation license, mesh asset
   * - ``mesh_filter_example.py``
     - Smooth a mesh. :doc:`/mesh_operations`
     - mesh-operation license, mesh asset
   * - ``camera_example.py``
     - Wrist camera: online check, intrinsics, RGB-D, point cloud.
       :doc:`/cameras_and_reconstruction`
     - real robot, camera
   * - ``reconstruction_example.py``
     - Live 3D reconstruction from a camera.
       :doc:`/cameras_and_reconstruction`
     - real robot, camera
   * - ``watch_scene_events_example.py``
     - Stream scene events with a callback and with a generator.
       :doc:`/scene_events`
     - server, and another client changing the scene
   * - ``numpy_conversion_example.py``
     - Round-trip every NumPy conversion. :doc:`/math_conversions`
     - nothing

``watch_scene_events_example.py`` only prints events, so it shows nothing
unless the scene changes while it runs. Run another example, or a ``pdk-scene``
command such as ``pdk-scene object create widget --box 0.1 0.1 0.1``, in a
second terminal.

The mesh asset
~~~~~~~~~~~~~~

Mesh examples load ``plane_1m_10x10.obj``. Copy
``examples/assets/plane_1m_10x10.obj`` to
``flexiv_pdk_data/user_data/meshes/plane_1m_10x10.obj`` on the server machine.
The examples refer to it as ``/home/flexiv/user_data/meshes/plane_1m_10x10.obj``,
which is where the containerized server sees that folder (see
:doc:`/install_server`). Adjust the path if your server is set up differently.

Real hardware
~~~~~~~~~~~~~

``system_setup_from_rdk_example.py``, ``camera_example.py`` and
``reconstruction_example.py`` connect to a real robot. Before running them:

* the robot must run Flexiv software package v3.11.3;
* enable RDK remote mode on the robot;
* change ``serial_number`` in the script to your robot's;
* for the camera examples, enable the camera in Noema Edge's AIConsole. The
  scripts use camera ID 9 on the robot's flange: change ``camera_id`` to match,
  and set the camera's parent to ``world`` for a camera that is not on the
  robot.

C++ example (CMake)
-------------------

``examples/cpp`` builds against an installed ``flexiv_pdk``
(:doc:`/install_for_cpp`). It has a C++ program for every Python example above,
under the same name and with the same requirements, so ``scene_example`` does
what ``scene_example.py`` does. ``eigen_conversion_example`` is the twin of
``numpy_conversion_example.py``: it round-trips every Eigen type through
``ToProto()`` and ``ToEigen()``, and needs no server.

.. code-block:: bash

   cd examples/cpp
   mkdir -p build && cd build
   cmake .. -DCMAKE_PREFIX_PATH=$HOME/pdk_install
   make -j4
   ./scene_example
   ./eigen_conversion_example

or, from ``examples/cpp``, in one step:
``FLEXIV_PDK_PREFIX=$HOME/pdk_install bash build.sh``. It builds into
``examples/cpp/build``.

Every C++ example connects to ``localhost:50052``. Set ``PDK_SERVER_ADDR`` to
use another server:

.. code-block:: bash

   PDK_SERVER_ADDR="192.168.1.100:50052" ./scene_example

The example's ``CMakeLists.txt``:

.. literalinclude:: /../../examples/cpp/CMakeLists.txt
   :language: cmake

ROS 2 examples
--------------

``examples/ros`` is an ament package, ``pdk_cpp_examples``, with two
executables: ``scene_example`` and ``point_to_point_path_example``.

.. code-block:: bash

   cd ros2_ws
   source /opt/ros/jazzy/setup.bash
   rosdep install --from-paths src/flexiv_pdk --ignore-src -r -y
   colcon build --paths src/flexiv_pdk src/flexiv_pdk/examples/ros
   source install/setup.bash

   ros2 run pdk_cpp_examples scene_example
   ros2 run pdk_cpp_examples point_to_point_path_example

Both are built from the sources in ``examples/cpp/src`` and read
``PDK_SERVER_ADDR`` in the same way. ``examples/ros/scripts`` has helpers to
run the build in an ``osrf/ros:jazzy-desktop`` Docker container.
