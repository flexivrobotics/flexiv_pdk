# Python Examples

Runnable scripts that show how to use the `flexiv.pdk` Python package, one
feature at a time. Each script creates its own workcell, so they can run in any
order.

## Before you start

1. Install the Python package and activate its environment, as
   [python/README.md](../../python/README.md) describes.
2. Set up and start the PDK server, as the
   [repository README](../../README.md#quick-start---server) describes.
3. Check that the two work together:

       pdk-scene version

Every example connects to `localhost:50052`. To use a server elsewhere, set
`PDK_SERVER_ADDR`:

    PDK_SERVER_ADDR="192.168.1.100:50052" python examples/python/scene_example.py

## Run an example

From the root of the repository:

    python examples/python/<example-name>.py

## The examples

### Scene and kinematics

No license or robot needed.

| Example                         | Shows how to                                                            |
| ------------------------------- | ----------------------------------------------------------------------- |
| `scene_example.py`              | Build a workcell with objects and two robot systems facing each other   |
| `components_service_example.py` | Query the robots and components the PDK knows, and create a custom tool |
| `system_kinematics_example.py`  | Compute forward and inverse kinematics of a robot system                |
| `watch_scene_events_example.py` | Receive scene changes as they happen, by callback or by generator       |
| `numpy_conversion_example.py`   | Convert between NumPy arrays and PDK messages. Needs no server          |

### Point-to-point path

Needs a `point_to_point_path` license.

| Example                          | Shows how to                                                               |
| -------------------------------- | -------------------------------------------------------------------------- |
| `point_to_point_path_example.py` | Plan collision-free paths among objects, with different collision settings |
| `system_pose_example.py`         | Save a pose computed by forward kinematics, then plan a path to it by name |

### Surface finish

Needs a `surface_finish` license and the example mesh (see [below](#copy-the-example-mesh)).

| Example                                        | Shows how to                                                                     |
| ---------------------------------------------- | -------------------------------------------------------------------------------- |
| `mesh_toolpath_raster_example.py`              | Create a raster tool path over a mesh                                            |
| `mesh_toolpath_sketch_example.py`              | Create a sketch tool path over a mesh                                            |
| `linear_path_trajectory_generation_example.py` | Create a tool path, solve the robot motion along it, and generate its trajectory |

### Mesh operations

Needs a `mesh_operation` license and the example mesh (see [below](#copy-the-example-mesh)).

| Example                           | Shows how to                |
| --------------------------------- | --------------------------- |
| `mesh_filter_example.py`          | Filter a mesh               |
| `mesh_area_extraction_example.py` | Extract an area from a mesh |

### With a real robot

Needs a Flexiv robot with RDK remote mode enabled. Set `serial_number` in the
script to your robot's.

| Example                            | Shows how to                                                           |
| ---------------------------------- | ---------------------------------------------------------------------- |
| `system_setup_from_rdk_example.py` | Add a robot system to the scene from a connected robot's configuration |
| `camera_example.py`                | Add a camera, then save and list its images and point clouds           |
| `reconstruction_example.py`        | Reconstruct the scene with a camera                                    |

The camera examples also need a camera enabled in Noema Edge's AIConsole. They
use camera ID 9 on the robot's flange: change `camera_id`, and set the camera's
parent to `world` for a camera that is not on the robot.

## Copy the example mesh

The surface finish and mesh operation examples load
[plane_1m_10x10.obj](../assets/plane_1m_10x10.obj) from the server's
`user_data/meshes/` folder. On the server's computer, from the root of the
repository:

    mkdir -p ../flexiv_pdk_data/user_data/meshes
    cp examples/assets/plane_1m_10x10.obj ../flexiv_pdk_data/user_data/meshes/

## When an example fails

A licensed example run without its license prints a failure whose message names
the license it needs. See
[Activate Licenses](https://flexivrobotics.github.io/flexiv_pdk/activate_licenses.html).

For anything else, read the server's log:

    pdk-scene log --level warning
