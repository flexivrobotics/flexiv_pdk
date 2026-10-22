# AGENTS.md - Guidance for generating Flexiv PDK client code

Scope: This file captures repository-specific, API-accurate knowledge for coding agents that generate Python or C++ applications using the Flexiv PDK (`flexiv.pdk` in Python, `flexiv::pdk` in C++).

## 0) Authoritative References
- PDK Manual: https://flexivrobotics.github.io/flexiv_pdk/
- API overview and service map: https://flexivrobotics.github.io/flexiv_pdk/api_overview.html
- Python package page: https://pypi.org/project/flexivpdk/
- Message and service definitions: `proto/flexiv/pdk/`

Use these sources for API behavior and field meaning when in doubt. The `.proto` comments are the authority for which fields are `[required]`.

## 0.1) How the PDK Is Built
- The PDK is a client library talking gRPC to a PDK server, which runs in Docker and holds all state.
- Every request and response is a Protocol Buffers message generated from `proto/flexiv/pdk/`.
- Python and C++ expose the same services, RPCs and messages. If Python docs are sparse, the `.proto` and the C++ headers in `include/flexiv/pdk/` use the same names.
- The client and the server must be the same version.

## 1) Preferred Script Pattern (Python)
- Use examples under `examples/python/` as style reference.
- Typical imports:
  - `import grpc`
  - `from flexiv.pdk import Client`
  - request and response messages from the `_pb2` module that mirrors the proto path, such as `from flexiv.pdk.workcell.workcell_service_pb2 import CreateRequest, NameRequest`
- Typical flow:
  1. `with Client("localhost:50052") as client:`. Creating the client does not contact the server; the first RPC does.
  2. Call RPCs as `client.<service>.stub.<Rpc>(request)`, for example `client.config.stub.Save(...)`.
  3. Create or load a workcell once with `client.workcell.stub.Create(...)` and `client.workcell.stub.Load(...)`.
  4. Save scene items with `client.config.stub.Save(SaveConfigRequest(<field>=...))`, setting exactly one field of its `config` oneof: `object`, `system`, `camera`, `coordinate`, `system_pose`, `object_pose`, `grasp_pose`, `surface_path` or `p2p_path`.
  5. Check `status.code` on every response (see section 3).
- For a re-runnable script, remove the workcell first and ignore the error if it does not exist, as the examples do.

## 1.1) Preferred Program Pattern (C++)
- Use examples under `examples/cpp/` and `examples/ros/` as style reference.
- `#include <flexiv/pdk/client.hpp>` and construct `flexiv::pdk::Client client("localhost:50052");`.
- Call RPCs as `client.<service>().stub-><Rpc>(&ctx, req, &res);`.
- Use a fresh `grpc::ClientContext` for every call. Reusing one fails.
- `Client` is neither copyable nor movable. Share it with `std::shared_ptr<flexiv::pdk::Client>`.
- `camera`, `mesh_operation` and `reconstruction` have no C++ accessor. Create their stubs from `client.channel()`, for example `flexiv::pdk::camera::CameraService::NewStub(client.channel())`.
- Link with `find_package(flexiv_pdk REQUIRED)` and `target_link_libraries(my_app PRIVATE flexiv::flexiv_pdk)`.

## 2) Service Map
| Python attribute      | C++ accessor            | Service                   | Notes                    |
| --------------------- | ----------------------- | ------------------------- | ------------------------ |
| `workcell`            | `workcell()`            | `WorkcellService`         | no workcell needed       |
| `config`              | `config()`              | `ConfigService`           | needs an active workcell |
| `frame`               | `frame()`               | `FrameService`            |                          |
| `scene_event`         | `scene_event()`         | `SceneEventService`       | server streaming         |
| `collision`           | `collision()`           | `CollisionService`        |                          |
| `system`              | `system()`              | `SystemService`           |                          |
| `system_config`       | `system_config()`       | `ComponentsService`       |                          |
| `system_state`        | `system_state()`        | `StateService`            |                          |
| `kinematics`          | `kinematics()`          | `KinematicsService`       |                          |
| `point_to_point_path` | `point_to_point_path()` | `PointToPointPathService` | licensed                 |
| `surface_finish`      | `surface_finish()`      | `SurfaceFinishService`    | licensed                 |
| `mesh_operation`      | none                    | `MeshOperationService`    | licensed                 |
| `camera`              | none                    | `CameraService`           |                          |
| `reconstruction`      | none                    | `ReconstructionService`   |                          |
| `license`             | `license()`             | `LicenseService`          | no workcell needed       |
| `version`             | `version()`             | `VersionService`          |                          |
| `log`                 | `log()`                 | `LogService`              | server streaming         |

Package names that do not follow the file path:
- `SurfaceFinishService` is in package `flexiv.pdk.surface_finish.generator`, although its file is `surface_finish/service.proto`.
- `MeshOperationService` is in package `flexiv.pdk`.

## 3) Critical Error-Handling Rule (Check Both Layers)
- A call fails at one of two layers, and generated code must check both:
  1. Transport: the server is unreachable, the request could not be parsed. Python raises `grpc.RpcError`; C++ returns a `grpc::Status` that is not `ok()`.
  2. Application: the server could not do what was asked. Nothing is raised. The response comes back with a non-zero `status.code`.
- A response object always exists after a successful gRPC call, even when the operation failed. Never treat its existence as success.
- Python check: `if hasattr(res, "status") and res.status.code != 0: raise RuntimeError(res.status.message)`.
- C++ check: `res.status().code() == flexiv::pdk::common::Status::OK`.
- Some `CameraService` and `ReconstructionService` RPCs return a bare `common.Status`. Check `.code` on the returned message itself.
- Status codes:
  - `0` `OK`
  - `1` `NOT_FOUND`: the named item does not exist
  - `2` `INVALID_ARGUMENT`: the request is malformed or a value is out of range
  - `3` `INTERNAL_ERROR`: the server failed while executing the request
  - `4` `FAILED_PRECONDITION`: most often, no workcell is loaded
  - `5` `PERMISSION_DENIED`: the service needs a license this computer does not have
- gRPC `INTERNAL` with no details means the client and the server disagree on the messages: install the client version that matches the server.

## 4) Critical Workcell Rule
- All scene data lives in a workcell. Exactly one workcell is active at a time.
- `ConfigService` and the scene services that build on it fail with `FAILED_PRECONDITION` (code 4) until a workcell is created or loaded.
- Create or load the workcell once per server session, then make as many scene calls as needed.
- `WorkcellService` and `LicenseService` do not need an active workcell.

## 5) Critical Quaternion Rule (Never Leave a Rotation Unset)
- Orientations are unit quaternions, `Quaternion(x, y, z, w)`.
- An unset quaternion is all zeros, not the identity. Always set `w=1.0` for no rotation.
- This applies to every `ConfigHeader.pose_in_parent`, `Visual.origin`, `Collision.origin` and `PathRefinement.rotation_offset`.
- Normalize quaternions before sending them.
- Python `to_numpy(Quaternion)` returns `[w, x, y, z]`, and `to_proto(array, Quaternion)` reads `[w, x, y, z]`, unlike the message's `x, y, z, w` field order.

## 6) Units and Frames
- All values are SI: metres, radians, newtons, newton-metres, kilograms. Prismatic joints are in metres.
- The scene is a tree of named frames rooted at `world`.
- `ConfigHeader` holds `name`, `parent` and `pose_in_parent`, and all three are required. The pose is relative to `parent`.
- A robot system `system_1` with a manipulator `arm` produces the frames `system_1`, `system_1.arm` and `system_1.arm.flange`. Use `system_1.arm.flange` as the TCP for kinematics and planning, and as the parent for a wrist camera.
- Joint vectors are plain lists ordered from base to flange: seven values for a Rizon arm.
- Points in path generator requests are in the parent object's frame unless the field documentation says world frame.
- `ConfigService.SetPose` changes the saved config. `FrameService.UpdatePose` moves the frame only and is not saved.

## 7) Proto3 Defaults
- Unset fields take their proto3 default: `0`, `""`, `false`, the first enum value, or an empty message.
- Some proto comments describe a different default, such as a boolean documented as "default true". Set every field that matters explicitly.
- Proto comments that mention `ConfigService.Add` mean `ConfigService.Save`. There is no `Add` RPC.

## 8) Feature-Specific Rules
- `KinematicsService.ComputeIK` and `PointToPointPathService.Plan` need the name of a saved collision configuration. Save one with `CollisionService` first.
- Collision pair names are objects or system components, such as `box_1` or `system_1.arm`. Get the valid names from `CollisionService.ListComponents`.
- `Mesh.filename` is resolved on the server, inside its container. Meshes in the customer's `flexiv_pdk_data/user_data/` are at `/home/flexiv/user_data/` there. Set the mesh `scale` to `(1, 1, 1)`.
- Surface finish runs in stages: `GenerateNominalPath`, `RefinePath`, `CreateRobotMotion`, then `GenerateRCATrajectoryFile`. Redoing a stage clears the results of later stages.
- `MeshOperationService` area extraction needs boundary points on the mesh surface, within 1 mm.
- Use only the services in section 2. The manual also documents an `ObjectCopyService`, which this release does not have.

## 9) Licensed Services
- Only three services need a license: `PointToPointPathService` (`point_to_point_path`), `SurfaceFinishService` (`surface_finish`) and `MeshOperationService` (`mesh_operation`).
- An unlicensed call returns `PERMISSION_DENIED` (code 5) in `status`, and nothing is raised. `status.message` names the license it needs.
- `client.license.stub.List` reports which licenses are installed before calling.
- A license installed with `LicenseService.Save` takes effect immediately. Do not tell the user to restart.
- A license is bound to the computer running the server and cannot be moved.

## 10) Output Style for Generated Code
- Prefer one self-contained runnable script per task.
- Take the server address as a parameter or from `PDK_SERVER_ADDR`, defaulting to `localhost:50052`.
- Check `status.code` after every RPC, and print `status.message` on failure.
- Include short comments only for non-obvious behavior.
- Before moving a real robot with PDK-computed motion, the user must follow the robot's safety instructions. Do not generate code that executes motion on a robot unless asked.

## 11) Command-Line Alternative
- `pdk-scene` ships with the Python package and drives a scene from the terminal with no code: `pdk-scene workcell create demo`, `pdk-scene object create widget --box 0.1 0.1 0.1 --pos 0.3 0 0.2`.
- Prefer it for one-off setup, inspection and debugging. Use the SDK for anything with real logic.
- `pdk-scene version` checks that the client and the server work together.
- `pdk-scene log --level warning` shows the server's recent warnings and errors. Read it before guessing why a call failed.
- `pdk-scene license status` shows the installed licenses.

## 12) Repository Anchors
- Python examples: `examples/python/`
- C++ examples: `examples/cpp/`
- ROS 2 examples: `examples/ros/`
- Example mesh: `examples/assets/plane_1m_10x10.obj`
- Python client: `python/flexiv/pdk/client.py`
- C++ client: `include/flexiv/pdk/client.hpp`
- NumPy conversions: `flexiv.pdk.spatial` (`to_numpy`, `to_proto`)
- Eigen conversions: `include/flexiv/pdk/spatial/eigen_conversion.hpp`
- Scene event subscriber: `flexiv.pdk.watch` (`Subscriber`, `watch`)
- Message and service definitions: `proto/flexiv/pdk/`
- CLI guide: `README_CLI.md`
- Repo readme and setup guide: `README.md`

## 13) Minimal Skeleton
```python
import os

import grpc

from flexiv.pdk import Client
from flexiv.pdk.config_header_pb2 import ConfigHeader
from flexiv.pdk.config_service_pb2 import ConfigType, ListConfigRequest, SaveConfigRequest
from flexiv.pdk.scene.object_pb2 import Object
from flexiv.pdk.spatial.geometry_pb2 import Quaternion, SE3Pose, Vector3
from flexiv.pdk.spatial.shape_pb2 import Box, Collision, Shape, Visual
from flexiv.pdk.workcell.workcell_service_pb2 import CreateRequest, NameRequest


def check(res, what):
    """Raises if a PDK response carries a failure status."""
    if hasattr(res, "status") and res.status.code != 0:
        raise RuntimeError(f"{what} failed: {res.status.message} (code {res.status.code})")
    return res


def pose(x=0.0, y=0.0, z=0.0):
    # w=1.0: an unset quaternion is all zeros, not the identity.
    return SE3Pose(position=Vector3(x=x, y=y, z=z), rotation=Quaternion(w=1.0))


def main():
    target = os.environ.get("PDK_SERVER_ADDR", "localhost:50052")
    with Client(target) as client:
        name = "my_workcell"
        if not client.workcell.stub.Exists(NameRequest(name=name)).exists:
            check(client.workcell.stub.Create(CreateRequest(name=name)), "Create workcell")
        check(client.workcell.stub.Load(NameRequest(name=name)), "Load workcell")

        box = Shape(box=Box(size=[0.1, 0.1, 0.1]))
        obj = Object(
            header=ConfigHeader(name="box_1", parent="world", pose_in_parent=pose(0.5, 0.0, 0.05)),
            visual=[Visual(origin=pose(), shape=box)],
            collision=[Collision(origin=pose(), shape=box)],
        )
        check(client.config.stub.Save(SaveConfigRequest(object=obj)), "Save object")

        res = check(client.config.stub.List(ListConfigRequest(type=ConfigType.CONFIG_TYPE_OBJECT)), "List objects")
        print("Objects:", list(res.names))


if __name__ == "__main__":
    try:
        main()
    except grpc.RpcError as e:
        print(f"gRPC {e.code().name}: {e.details()}")
```
