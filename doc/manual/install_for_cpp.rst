Install for C++
===============

Install the C++ client library for use with CMake or ROS 2. You need a running
**PDK server** to connect to; see :doc:`/install_server`.

.. note::

   The client must have the same major and minor version as the server.

Use with CMake
--------------

Requirements: CMake 3.16.3+, a C++17 compiler, Eigen3, Protobuf and gRPC, on
Ubuntu 22.04, 24.04 or 26.04 (x86_64).

1. Clone the PDK repository and install the native dependencies:

   .. code-block:: bash

      git clone https://github.com/flexivrobotics/flexiv_pdk.git
      cd flexiv_pdk
      bash install_dependencies.sh

   This installs ``cmake pkg-config libeigen3-dev libprotobuf-dev libgrpc++-dev
   protobuf-compiler-grpc`` from apt.

2. From the repository root, configure, build and install the package to a
   prefix of your choice:

   .. code-block:: bash

      mkdir build && cd build
      cmake .. -DCMAKE_INSTALL_PREFIX=$HOME/pdk_install
      make -j
      make install

   The ``flexiv_pdk`` package ships a pre-built ``libflexiv_pdk.so`` for your
   platform (for example ``ubuntu-22.04-x86_64``). CMake downloads it from the
   GitHub release and verifies its checksum. Useful options:

   ``-DFLEXIV_PDK_LIBRARY_DIR=<dir>``
      Use a ``libflexiv_pdk.<platform>.so`` you already have, for offline builds.
   ``-DFLEXIV_PDK_PLATFORM=<platform>``
      Override the detected platform name.

   .. warning::

      Configuration fails if the Protobuf found on your system does not have
      the same *major.minor* version that the library was built against. Use
      the Protobuf that ships with your Ubuntu release.

3. Use it from your project:

   .. code-block:: cmake

      cmake_minimum_required(VERSION 3.16.3)
      project(my_app LANGUAGES CXX)

      find_package(flexiv_pdk REQUIRED)

      add_executable(my_app main.cpp)
      target_link_libraries(my_app PRIVATE flexiv::flexiv_pdk)
      set_target_properties(my_app PROPERTIES CXX_STANDARD 17 CXX_STANDARD_REQUIRED ON)

   Point CMake at the install with ``-DCMAKE_PREFIX_PATH=$HOME/pdk_install``
   (or ``-Dflexiv_pdk_DIR=...``). ``CMAKE_INSTALL_PREFIX`` only controls where
   *your* project installs.

   The ``flexiv::flexiv_pdk`` target brings in Eigen3, gRPC (``gRPC::grpc++``,
   or ``grpc++`` through pkg-config when no gRPC CMake config exists) and
   Protobuf transitively.

4. Run your program. ``libflexiv_pdk.so`` must be found when it starts:

   * A program run from its CMake build tree finds it by RPATH, with nothing
     else to do.
   * A program you install with ``cmake --install`` needs one of:

     * ``set_target_properties(my_app PROPERTIES INSTALL_RPATH $ENV{HOME}/pdk_install/lib)``
     * ``export LD_LIBRARY_PATH=$HOME/pdk_install/lib:$LD_LIBRARY_PATH``
     * installing the PDK to ``/usr/local`` and running ``sudo ldconfig``

   In a ROS 2 workspace, ``source install/setup.bash`` puts the library on
   ``LD_LIBRARY_PATH``.

Use with ROS 2
--------------

Supported distributions: Humble and Jazzy.

Clone the package into your workspace once and install its dependencies:

.. code-block:: bash

   cd ros2_ws/src
   git clone https://github.com/flexivrobotics/flexiv_pdk.git
   source /opt/ros/jazzy/setup.bash
   rosdep update
   rosdep install --from-paths flexiv_pdk --ignore-src -r -y

Build:

.. code-block:: bash

   cd ros2_ws
   source /opt/ros/jazzy/setup.bash
   colcon build
   source install/setup.bash

In your own ament package:

.. code-block:: cmake

   find_package(ament_cmake REQUIRED)
   find_package(flexiv_pdk REQUIRED)

   add_executable(my_node src/my_node.cpp)
   ament_target_dependencies(my_node PUBLIC flexiv_pdk)

and add ``<depend>flexiv_pdk</depend>`` to your ``package.xml``.

Use from other languages
------------------------

Every service is defined in ``proto/flexiv/pdk/``. Generate client stubs for
your language with its gRPC code generator and connect to the server address
(default ``localhost:50052``) over an insecure channel.
