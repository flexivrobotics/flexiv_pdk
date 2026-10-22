"""``camera`` commands: scene cameras (ConfigService-backed).

``list`` / ``get`` / ``remove`` come from :func:`config_group`; this module adds
the camera-specific ``create`` verb and the ``get`` formatter.
"""
import click

from flexiv.pdk.config_header_pb2 import ConfigHeader
from flexiv.pdk.config_service_pb2 import ConfigType, SaveConfigRequest
from flexiv.pdk.scene.camera_pb2 import Camera

from .._common import check, open_client, rpc, se3
from .._config_resource import config_group


def _format_camera(cam):
    """Render a Camera for `camera get` -> (json-dict, human text lines)."""
    pose = cam.header.pose_in_parent
    data = {
        "name": cam.header.name,
        "parent": cam.header.parent,
        "position": [pose.position.x, pose.position.y, pose.position.z],
        "quaternion": [pose.rotation.x, pose.rotation.y, pose.rotation.z, pose.rotation.w],
        "camera_id": cam.camera_id,
        "far_width": cam.far_width,
        "far_height": cam.far_height,
        "far_distance": cam.far_distance,
        "near_distance": cam.near_distance,
    }
    lines = [
        f"Camera: {data['name']} (parent {data['parent']}, id {data['camera_id']})",
        f"Position:   {data['position']}",
        f"Quaternion: {data['quaternion']}",
        f"Far plane:  {data['far_width']} x {data['far_height']} @ {data['far_distance']} m",
        f"Near plane: {data['near_distance']} m",
    ]
    return data, lines


camera_group = config_group(
    "camera", ConfigType.CONFIG_TYPE_CAMERA,
    help="Create, list, and remove scene cameras (requires an active workcell).",
    label="cameras", json_key="cameras",
    get_field="camera", formatter=_format_camera,
)


@camera_group.command("create")
@click.argument("name")
@click.option("--parent", default="world", show_default=True, help="Parent frame name.")
@click.option("--pos", nargs=3, type=float, default=(0.0, 0.0, 0.0),
              help="Position x y z (m).")
@click.option("--quat", nargs=4, type=float, default=(0.0, 0.0, 0.0, 1.0),
              help="Orientation quaternion x y z w.")
@click.option("--camera-id", type=int, default=0, show_default=True, help="Camera ID.")
@click.option("--far-width", type=float, default=1.0, show_default=True,
              help="Far-plane width (m).")
@click.option("--far-height", type=float, default=1.0, show_default=True,
              help="Far-plane height (m).")
@click.option("--far-distance", type=float, default=2.0, show_default=True,
              help="Distance to the far plane (m).")
@click.option("--near-distance", type=float, default=0.1, show_default=True,
              help="Distance to the near plane (m).")
@click.pass_context
@rpc
def camera_create(ctx, name, parent, pos, quat, camera_id,
                  far_width, far_height, far_distance, near_distance):
    """Create camera NAME at the given pose with view-frustum parameters."""
    camera = Camera(
        header=ConfigHeader(name=name, parent=parent, pose_in_parent=se3(pos, quat)),
        camera_id=camera_id,
        far_width=far_width, far_height=far_height,
        far_distance=far_distance, near_distance=near_distance,
    )
    with open_client(ctx) as client:
        check(client.config.stub.Save(SaveConfigRequest(camera=camera)), "Create camera")
    click.echo(f"Created camera {name!r} on {parent!r} (id {camera_id}).")
