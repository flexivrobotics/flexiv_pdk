"""``surface-path`` commands: surface-finish paths (ConfigService-backed).

A surface-finish path (CONFIG_TYPE_SURFACE_PATH, a ``surface_finish.Path``) is a
sequence of Cartesian waypoints attached to a parent object; the waypoints are
expressed in that object's frame. This command builds a straight-line path from
a ``ManualPath`` of interpolated waypoints and saves it via ConfigService.

``list`` / ``get`` / ``remove`` come from :func:`config_group`; this module adds
the ``create`` verb and the ``get`` formatter.
"""
import click

from flexiv.pdk.config_header_pb2 import ConfigHeader
from flexiv.pdk.config_service_pb2 import ConfigType, SaveConfigRequest
from flexiv.pdk.spatial.waypoint_pb2 import CartesianWaypoint
from flexiv.pdk.surface_finish.path_pb2 import Path

from .._common import check, open_client, rpc, se3
from .._config_resource import config_group


def _line_waypoints(start, end, count, quat):
    """Return `count` CartesianWaypoints evenly spaced from start to end (parent frame)."""
    waypoints = []
    for i in range(count):
        t = i / (count - 1)
        pos = tuple(s + (e - s) * t for s, e in zip(start, end))
        waypoints.append(CartesianWaypoint(pose=se3(pos, quat)))
    return waypoints


def _format_surface_path(path):
    """Render a surface_finish.Path for `surface-path get` -> (json-dict, text lines)."""
    waypoints = list(path.manual_path.cartesian) or list(path.nominal_cartesian)
    positions = [[w.pose.position.x, w.pose.position.y, w.pose.position.z] for w in waypoints]
    data = {
        "name": path.header.name,
        "parent": path.header.parent,
        "source": path.WhichOneof("nominal"),
        "waypoints": positions,
    }
    lines = [f"Surface-finish path: {data['name']} "
             f"(parent {data['parent']}, source {data['source']})"]
    lines += [f"  waypoint {i}: {p}" for i, p in enumerate(positions)]
    return data, lines


surface_path_group = config_group(
    "surface-path", ConfigType.CONFIG_TYPE_SURFACE_PATH,
    help="Create, list, and remove surface-finish paths (requires an active workcell).",
    label="surface-finish paths", json_key="surface_paths",
    get_field="surface_path", formatter=_format_surface_path,
)


@surface_path_group.command("create")
@click.argument("name")
@click.option("--parent", required=True,
              help="Object the path is attached to; waypoints are in this frame.")
@click.option("--from", "start", nargs=3, type=float, default=(0.0, 0.0, 0.0),
              show_default=True, help="Line start point x y z (m) in the parent frame.")
@click.option("--to", "end", nargs=3, type=float, default=(0.1, 0.0, 0.0),
              show_default=True, help="Line end point x y z (m) in the parent frame.")
@click.option("--points", type=int, default=2, show_default=True,
              help="Number of waypoints sampled along the line (>= 2).")
@click.option("--quat", nargs=4, type=float, default=(0.0, 0.0, 0.0, 1.0),
              show_default=True, help="Orientation quaternion x y z w for every waypoint.")
@click.pass_context
@rpc
def surface_path_create(ctx, name, parent, start, end, points, quat):
    """Create straight-line surface-finish path NAME on object --parent, from --from to --to."""
    if points < 2:
        raise click.UsageError("--points must be at least 2.")
    waypoints = _line_waypoints(start, end, points, quat)

    path = Path(header=ConfigHeader(name=name, parent=parent))
    path.manual_path.cartesian.extend(waypoints)  # manual (straight-line) nominal source
    path.nominal_cartesian.extend(waypoints)       # stage-1 waypoint result

    with open_client(ctx) as client:
        check(client.config.stub.Save(SaveConfigRequest(surface_path=path)),
              "Create surface-finish path")
    click.echo(f"Created surface-finish path {name!r} on {parent!r} "
               f"({points} waypoints from {list(start)} to {list(end)}).")
