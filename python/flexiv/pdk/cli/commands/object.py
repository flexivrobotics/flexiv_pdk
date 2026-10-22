"""``object`` commands: scene objects (ConfigService-backed).

``list`` / ``get`` / ``remove`` come from :func:`config_group`; this module adds
the object-specific ``create`` and ``move`` verbs and the ``get`` formatter.
"""
import click

from flexiv.pdk.config_header_pb2 import ConfigHeader
from flexiv.pdk.config_service_pb2 import (
    ConfigType,
    SaveConfigRequest,
    SetPoseRequest,
)
from flexiv.pdk.scene.object_pb2 import Object

from .._common import check, open_client, rpc, se3
from .._config_resource import config_group


def _add_box_shape(obj, size):
    """Attach an identical box visual + collision to obj (mirrors the server model)."""
    for holder in (obj.visual.add(), obj.collision.add()):
        holder.origin.rotation.w = 1.0
        holder.shape.box.size.extend([float(size[0]), float(size[1]), float(size[2])])


def _set_color(obj, rgba):
    """Give every visual of obj the color rgba."""
    for visual in obj.visual:
        visual.material.rgba[:] = [float(value) for value in rgba]


def _add_mesh_shape(obj, filename):
    """Attach an identical mesh visual + collision to obj."""
    for holder in (obj.visual.add(), obj.collision.add()):
        holder.origin.rotation.w = 1.0
        holder.shape.mesh.filename = filename
        holder.shape.mesh.scale.x = 1.0
        holder.shape.mesh.scale.y = 1.0
        holder.shape.mesh.scale.z = 1.0


def _shape_summary(shape):
    """One-line description of a Shape oneof for `object get`."""
    kind = shape.WhichOneof("type")
    if kind == "box":
        return {"box": list(shape.box.size)}
    if kind == "mesh":
        return {"mesh": shape.mesh.filename}
    return {kind or "none": None}


def _format_object(obj):
    """Render an Object for `object get` -> (json-dict, human text lines)."""
    pose = obj.header.pose_in_parent
    data = {
        "name": obj.header.name,
        "parent": obj.header.parent,
        "position": [pose.position.x, pose.position.y, pose.position.z],
        "quaternion": [pose.rotation.x, pose.rotation.y, pose.rotation.z, pose.rotation.w],
        "shapes": [_shape_summary(v.shape) for v in obj.visual],
        "colors": [list(v.material.rgba) or None for v in obj.visual],
    }
    lines = [
        f"Object: {data['name']} (parent {data['parent']})",
        f"Position:   {data['position']}",
        f"Quaternion: {data['quaternion']}",
    ]
    lines += [f"Visual: {shape}" + (f" color {color}" if color else "")
              for shape, color in zip(data["shapes"], data["colors"])]
    return data, lines


object_group = config_group(
    "object", ConfigType.CONFIG_TYPE_OBJECT,
    help="Create, move, inspect, and remove scene objects (requires an active workcell).",
    label="objects", json_key="objects",
    get_field="object", formatter=_format_object,
)


@object_group.command("create")
@click.argument("name")
@click.option("--parent", default="world", show_default=True, help="Parent frame name.")
@click.option("--pos", nargs=3, type=float, default=(0.0, 0.0, 0.0),
              help="Position x y z (m).")
@click.option("--quat", nargs=4, type=float, default=(0.0, 0.0, 0.0, 1.0),
              help="Orientation quaternion x y z w.")
@click.option("--box", nargs=3, type=float, default=None,
              help="Box visual/collision size LX LY LZ (m).")
@click.option("--mesh", type=str, default=None,
              help="Mesh file path (server-visible) for the visual/collision.")
@click.option("--color", nargs=4, type=float, default=None,
              help="Visual color R G B A, each 0 to 1. Needs --box or --mesh.")
@click.pass_context
@rpc
def object_create(ctx, name, parent, pos, quat, box, mesh, color):
    """Create scene object NAME with an optional --box or --mesh shape."""
    if box and mesh:
        raise click.UsageError("Use only one of --box or --mesh.")
    if color and not (box or mesh):
        raise click.UsageError("--color needs --box or --mesh.")

    obj = Object(header=ConfigHeader(
        name=name, parent=parent, pose_in_parent=se3(pos, quat)))
    if box:
        _add_box_shape(obj, box)
    elif mesh:
        _add_mesh_shape(obj, mesh)
    if color:
        _set_color(obj, color)

    with open_client(ctx) as client:
        check(client.config.stub.Save(SaveConfigRequest(object=obj)), "Create object")
    click.echo(f"Created object {name!r}.")


@object_group.command("move")
@click.argument("name")
@click.option("--pos", nargs=3, type=float, default=(0.0, 0.0, 0.0),
              help="New position x y z (m).")
@click.option("--quat", nargs=4, type=float, default=(0.0, 0.0, 0.0, 1.0),
              help="New orientation quaternion x y z w.")
@click.pass_context
@rpc
def object_move(ctx, name, pos, quat):
    """Move object NAME to a new pose (persisted; emits CHANGE_UPDATED)."""
    with open_client(ctx) as client:
        check(client.config.stub.SetPose(SetPoseRequest(
            type=ConfigType.CONFIG_TYPE_OBJECT, name=name, pose=se3(pos, quat))),
            "Move object")
    click.echo(f"Moved object {name!r}.")
