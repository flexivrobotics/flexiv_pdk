"""``coordinate`` commands: named coordinate frames (ConfigService-backed).

A Coordinate is a named frame (pose relative to a parent), similar to a URDF
link. ``list`` / ``get`` / ``remove`` come from :func:`config_group`; this module
adds the ``create`` verb and the ``get`` formatter.
"""
import click

from flexiv.pdk.config_header_pb2 import ConfigHeader
from flexiv.pdk.config_service_pb2 import ConfigType, SaveConfigRequest
from flexiv.pdk.scene.coordinate_pb2 import Coordinate
from flexiv.pdk.spatial.geometry_pb2 import Vector3

from .._common import check, open_client, rpc, se3
from .._config_resource import config_group


def _format_coordinate(coord):
    """Render a Coordinate for `coordinate get` -> (json-dict, human text lines)."""
    pose = coord.header.pose_in_parent
    scale = coord.scale
    data = {
        "name": coord.header.name,
        "parent": coord.header.parent,
        "position": [pose.position.x, pose.position.y, pose.position.z],
        "quaternion": [pose.rotation.x, pose.rotation.y, pose.rotation.z, pose.rotation.w],
        "scale": [scale.x, scale.y, scale.z],
    }
    lines = [
        f"Coordinate: {data['name']} (parent {data['parent']})",
        f"Position:   {data['position']}",
        f"Quaternion: {data['quaternion']}",
        f"Scale:      {data['scale']}",
    ]
    return data, lines


coordinate_group = config_group(
    "coordinate", ConfigType.CONFIG_TYPE_COORDINATE,
    help="Create, list, and remove named coordinate frames (requires an active workcell).",
    label="coordinates", json_key="coordinates",
    get_field="coordinate", formatter=_format_coordinate,
)


@coordinate_group.command("create")
@click.argument("name")
@click.option("--parent", default="world", show_default=True, help="Parent frame name.")
@click.option("--pos", nargs=3, type=float, default=(0.0, 0.0, 0.0),
              help="Position x y z (m).")
@click.option("--quat", nargs=4, type=float, default=(0.0, 0.0, 0.0, 1.0),
              help="Orientation quaternion x y z w.")
@click.option("--scale", nargs=3, type=float, default=None,
              help="Optional display scale x y z (m).")
@click.pass_context
@rpc
def coordinate_create(ctx, name, parent, pos, quat, scale):
    """Create coordinate frame NAME at the given pose relative to --parent."""
    coord = Coordinate(
        header=ConfigHeader(name=name, parent=parent, pose_in_parent=se3(pos, quat)))
    if scale:
        coord.scale.CopyFrom(Vector3(x=scale[0], y=scale[1], z=scale[2]))

    with open_client(ctx) as client:
        check(client.config.stub.Save(SaveConfigRequest(coordinate=coord)), "Create coordinate")
    click.echo(f"Created coordinate {name!r} on {parent!r}.")
