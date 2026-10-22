# C++ Examples

Programs that show how to use the `flexiv_pdk` C++ library, one feature at a time. Each one
does the same as the Python example of the same name in [../python](../python/README.md), and
creates its own workcell, so they can run in any order.

## Prerequisites

- `flexiv_pdk` is installed to `~/pdk_install`, as in the [repository README](../../README.md).
- A PDK server is running and reachable (default: `localhost:50052`), for every example except
  `eigen_conversion_example`.

## Build

From this directory (`examples/cpp`):

```bash
mkdir -p build
cd build
cmake .. -DCMAKE_PREFIX_PATH=$HOME/pdk_install
make -j4
```

Or do the same in one step:

```bash
FLEXIV_PDK_PREFIX=$HOME/pdk_install bash build.sh
```

*Note: If you installed the SDK somewhere else, use that path in place of `$HOME/pdk_install`.*

## Run

From this directory:

```bash
./build/<example-name>
```

The default server address is `localhost:50052`. To use a server elsewhere, set
`PDK_SERVER_ADDR`:

```bash
PDK_SERVER_ADDR="192.168.1.100:50052" ./build/scene_example
```

## The examples

### Scene and kinematics

No license or robot needed.

| Example                      | Shows how to                                                            |
| ---------------------------- | ----------------------------------------------------------------------- |
| `scene_example`              | Build a workcell with objects and two robot systems facing each other   |
| `components_service_example` | Query the robots and components the PDK knows, and create a custom tool |
| `system_kinematics_example`  | Compute forward and inverse kinematics of a robot system                |
| `watch_scene_events_example` | Receive scene changes as they happen, by callback or by a blocking read |
| `eigen_conversion_example`   | Convert between Eigen types and PDK messages. Needs no server           |

### Point-to-point path

Needs a `point_to_point_path` license.

| Example                       | Shows how to                                                               |
| ----------------------------- | -------------------------------------------------------------------------- |
| `point_to_point_path_example` | Plan collision-free paths among objects, with different collision settings |
| `system_pose_example`         | Save a pose computed by forward kinematics, then plan a path to it by name |

### Surface finish

Needs a `surface_finish` license and the example mesh (see [below](#copy-the-example-mesh)).

| Example                                     | Shows how to                                                                     |
| ------------------------------------------- | -------------------------------------------------------------------------------- |
| `mesh_toolpath_raster_example`              | Create a raster tool path over a mesh                                            |
| `mesh_toolpath_sketch_example`              | Create a sketch tool path over a mesh                                            |
| `linear_path_trajectory_generation_example` | Create a tool path, solve the robot motion along it, and generate its trajectory |

### Mesh operations

Needs a `mesh_operation` license and the example mesh (see [below](#copy-the-example-mesh)).

| Example                        | Shows how to                |
| ------------------------------ | --------------------------- |
| `mesh_filter_example`          | Filter a mesh               |
| `mesh_area_extraction_example` | Extract an area from a mesh |

### With a real robot

Needs a Flexiv robot with RDK remote mode enabled. Set `serial_number` in the source to your
robot's, and rebuild.

| Example                         | Shows how to                                                           |
| ------------------------------- | ---------------------------------------------------------------------- |
| `system_setup_from_rdk_example` | Add a robot system to the scene from a connected robot's configuration |
| `camera_example`                | Add a camera, then save and list its images and point clouds           |
| `reconstruction_example`        | Reconstruct the scene with a camera                                    |

The camera examples also need a camera enabled in Noema Edge's AIConsole. They use camera ID 9 on
the robot's flange: change the camera ID, and set the camera's parent to `world` for a camera that
is not on the robot.

## Copy the example mesh

The surface finish and mesh operation examples load
[plane_1m_10x10.obj](../assets/plane_1m_10x10.obj) from the server's `user_data/meshes/` folder.
On the server's computer, from the root of the repository:

    mkdir -p ../flexiv_pdk_data/user_data/meshes
    cp examples/assets/plane_1m_10x10.obj ../flexiv_pdk_data/user_data/meshes/

## When an example fails

A licensed example run without its license prints a failure whose message names the license it
needs. See [Activate Licenses](https://flexivrobotics.github.io/flexiv_pdk/activate_licenses.html).

For anything else, read the server's log:

    pdk-scene log --level warning
