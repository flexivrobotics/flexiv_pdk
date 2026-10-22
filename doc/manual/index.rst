Flexiv PDK Manual
=================

`PDK repository <https://github.com/flexivrobotics/flexiv_pdk>`_

Flexiv PDK (Planning Development Kit) is a client SDK for building robotic
applications on top of a running PDK server. It sets up workcells of robots and
objects, generates tool paths and the robot motion that follows them, and plans
collision-free point-to-point motion. Python, C++ (CMake and ROS 2) and the ``pdk-scene`` command-line
tool are provided, all talking to the server over gRPC.

This manual documents release |version_full|.

.. important::
   The PDK client and server must have the same major and minor version.
   Before moving real robots with motion computed by the PDK, you must carefully
   read through all documents shipped with the robot and strictly follow **all
   safety instructions** detailed in these documents.

Overview
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Overview

   what_is_pdk
   environment_compatibility

Installation
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Installation

   install_server
   install_for_python
   install_for_cpp

First Time Setup
-----------------

.. toctree::
   :maxdepth: 2
   :caption: First Time Setup

   activate_licenses
   build_your_first_scene
   verify_with_example_programs

Flexiv PDK
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Flexiv PDK

   api_overview
   error_handling
   workcells
   scene_model
   units_and_conventions

Applications
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Applications

   scene_setup
   systems_and_components
   collision
   kinematics
   point_to_point_path
   surface_finish
   mesh_operations
   cameras_and_reconstruction
   scene_events
   math_conversions

Command-Line Tool
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Command-Line Tool

   pdk_scene_cli

API Reference
-----------------

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   services
   messages
   python_api
   cpp_api

Troubleshooting
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Troubleshooting

   troubleshooting
