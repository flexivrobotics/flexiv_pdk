Environment Compatibility
=========================

The PDK client runs on the following languages, build systems and operating systems.

Supported languages
-------------------

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Language
     - Support
     - Notes
   * - Python 3.10+
     - Full
     - ``flexivpdk`` package (:doc:`/install_for_python`); NumPy conversion
       helpers; ``pdk-scene`` CLI.
   * - C++17, CMake 3.16.3+
     - Full
     - ``find_package(flexiv_pdk)``; Eigen3 conversion helpers.
   * - C++17, ROS 2 (Humble, Jazzy)
     - Full
     - ament package ``flexiv_pdk``. Same services as C++ with CMake.
   * - TypeScript / JavaScript
     - Helpers
     - Three.js conversion helpers in ``typescript/``. Generate the gRPC stubs
       from ``proto/flexiv/pdk/``.
   * - Any other gRPC language
     - Possible
     - Generate stubs from ``proto/flexiv/pdk/`` with your language's gRPC tools.

Supported operating systems
---------------------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Component
     - Operating systems
   * - PDK server
     - Ubuntu 22.04, x86_64, with Docker (:doc:`/install_server`). Other Linux
       systems with Docker are untested.
   * - Python client
     - Any OS with Python 3.10+.
   * - C++ client
     - Ubuntu 22.04, 24.04 and 26.04, x86_64 (pre-built
       ``libflexiv_pdk.<platform>.so``).

Version compatibility
---------------------

A client works with a server of the same major and minor version. Both the
Python package and the C++ package carry the same version number
(|version_full| for this manual). ``pdk-scene version`` and
``VersionService.GetVersion`` report the server version and whether it
considers your client compatible; see :doc:`/services`.
