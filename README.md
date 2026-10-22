# Flexiv PDK

[![Manual](https://github.com/flexivrobotics/flexiv_pdk/actions/workflows/docs.yml/badge.svg)](https://flexivrobotics.github.io/flexiv_pdk/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0.html)

Flexiv PDK (Planning Development Kit) is a development toolkit for planning the
motion of Flexiv robots. Your application describes a workcell of robots,
objects and cameras, and the PDK computes the motion: inverse kinematics,
collision-free point-to-point paths, and tool paths over a part's surface with
the robot motion that follows them. It works alongside
[Flexiv RDK](https://github.com/flexivrobotics/flexiv_rdk), which executes
motion on the robot.

```
   Your application                        Docker
+---------------------+              +-----------------+
| Python  flexiv.pdk  |     gRPC     |                 |
| C++     flexiv::pdk | <----------> |   PDK server    |
| CLI     pdk-scene   |              |                 |
+---------------------+              +-----------------+
```

## References

The [Flexiv PDK Manual](https://flexivrobotics.github.io/flexiv_pdk/) is the main
reference, with tutorials, every service, and the Python and C++ API.

## What the PDK does

| Feature             | What it does                                                                                                            | License  |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------- | -------- |
| Scene setup         | Build a workcell of robot systems, objects, cameras and coordinate frames, and query or move anything in it             | Free     |
| Kinematics          | Forward and inverse kinematics of a robot system, for poses in the scene                                                | Free     |
| Perception          | Capture camera images and point clouds, and reconstruct the scene                                                       | Free     |
| Point-to-point path | Plan collision-free robot motion between joint positions or saved poses, optionally carrying a grasped object           | Licensed |
| Surface finish      | Create a tool path on an object, from CAD edges or faces or from its mesh, and compute the robot motion that follows it | Licensed |
| Mesh operations     | Process an object's mesh: smoothing, filtering, extracting its largest region                                           | Licensed |

Contact Flexiv to get a license for the licensed features. A license is bound to
the computer running the PDK server, and without one every free feature still
runs. To install a license, see
[Activate Licenses](https://flexivrobotics.github.io/flexiv_pdk/activate_licenses.html).

## Environment compatibility

Use the same release of this repository for the server and your application.

### Client

| Language             | Platform                                                                         |
| -------------------- | -------------------------------------------------------------------------------- |
| Python               | Python 3.10+, any OS                                                             |
| C++ with CMake       | Ubuntu 22.04, 24.04 or 26.04, x86_64                                             |
| C++ with ROS 2       | Humble or Jazzy, x86_64                                                          |
| Other gRPC languages | Any OS, from the `.proto` files: see [Use from other languages][other-languages] |

[other-languages]: https://flexivrobotics.github.io/flexiv_pdk/install_for_cpp.html#use-from-other-languages

### Server

| Requirement | Server                                                                                            |
| ----------- | ------------------------------------------------------------------------------------------------- |
| OS          | Ubuntu 22.04                                                                                      |
| Platform    | x86_64                                                                                            |
| Needs       | [Docker Engine][docker-engine], your user in the [docker group][docker-group], 21 GB of free disk |
| Optional    | TPM 2.0 chip for licensed features; NVIDIA GPU for faster motion planning                         |

[docker-engine]: https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository
[docker-group]: https://docs.docker.com/engine/install/linux-postinstall/

## Important notice

Before moving a real robot with motion computed by the PDK, read every document
shipped with the robot and follow all of its safety instructions.

## Quick start

### 1. Download the PDK

Download and unpack a release:

    curl -L https://github.com/flexivrobotics/flexiv_pdk/archive/refs/tags/v<version>.tar.gz | tar -xz
    cd flexiv_pdk-<version>

Replace `<version>` with a release from the
[releases page](https://github.com/flexivrobotics/flexiv_pdk/releases), such as
`1.0.0`. For ROS 2, unpack it in your workspace's `src/` folder. You can also
clone this repository at the release's tag instead.

### 2. Set up and start the server

In the unpacked folder:

    bash server/setup_server.sh
    bash server/run_server.sh

Setup downloads about 14 GB. If it is interrupted, run it again: it keeps what
it already has. Add `--gpu` to `setup_server.sh` to use an NVIDIA GPU, which
needs the NVIDIA driver and the
[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

The server needs a desktop session. It listens on port 50052, and the examples
connect to it at `localhost:50052`. Stop it with Ctrl+C, then
`bash server/docker_stop.sh`. Your workcells and licenses are kept in
`flexiv_pdk_data/`, beside the unpacked folder. See
[server/README.md](server/README.md) for more.

### 3. Install the client

#### Python

Install `flexivpdk` and its dependencies from PyPI:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install "flexivpdk==<version>"

Use the `<version>` you downloaded, such as `1.0.0`; it must match the server's.

#### C++ with CMake

In the unpacked folder, install the dependencies and the PDK:

    bash install_dependencies.sh
    mkdir build && cd build
    cmake .. -DCMAKE_INSTALL_PREFIX=$HOME/pdk_install
    cmake --install .

Configuring downloads the PDK library for your platform from the GitHub release.
Then in your project's `CMakeLists.txt`:

```cmake
find_package(flexiv_pdk REQUIRED)
target_link_libraries(my_app PRIVATE flexiv::flexiv_pdk)
```

and configure it with `-DCMAKE_PREFIX_PATH=$HOME/pdk_install`. To run a program
you installed, or to install without network access, see
[Install for C++](https://flexivrobotics.github.io/flexiv_pdk/install_for_cpp.html).

#### C++ with ROS 2

In your workspace, with `<distro>` as `humble` or `jazzy`:

    source /opt/ros/<distro>/setup.bash
    rosdep update
    rosdep install --from-paths src --ignore-src -r -y
    colcon build
    source install/setup.bash

Then depend on it like any other package:

```xml
<depend>flexiv_pdk</depend>
```

```cmake
find_package(flexiv_pdk REQUIRED)
ament_target_dependencies(my_node flexiv_pdk)
```

### 4. Check the connection

With the server running and the Python package installed:

    pdk-scene version

It prints the client and server versions, and says whether they work together.

### Next steps

- A first scene, step by step:
  [Build Your First Scene](https://flexivrobotics.github.io/flexiv_pdk/build_your_first_scene.html)
- Python: [python/README.md](python/README.md) and [examples/python](examples/python/README.md)
- C++: [examples/cpp](examples/cpp/README.md) and [examples/ros](examples/ros/ROS_EXAMPLE_README.md)
- Drive a scene from the terminal, with no code: [README_CLI.md](README_CLI.md)

## Upgrade

Stop the server, download and unpack the new release beside the old one, and
set up the server from the new folder:

    curl -L https://github.com/flexivrobotics/flexiv_pdk/archive/refs/tags/v<version>.tar.gz | tar -xz
    cd flexiv_pdk-<version>
    bash server/setup_server.sh

If you cloned this repository, check out the new release's tag instead. Then
install the client of the same release. Your workcells and licenses in
`flexiv_pdk_data/` are kept, as every release beside it uses that folder.

## License

The code in this repository is released under the [Apache 2.0 license](LICENSE).
