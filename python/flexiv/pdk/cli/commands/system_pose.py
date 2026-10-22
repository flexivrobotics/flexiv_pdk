"""``system-pose`` commands: full-state robot poses (ConfigService-backed).

A system pose is a TargetWaypoint: a named Cartesian pose paired with the joint
positions that realize it for a system. ``list`` / ``get`` / ``remove`` come from
:func:`config_group`; this module adds the ``create`` verb and the ``get``
formatter.

Note: the server refuses to overwrite an existing system pose — ``remove`` it
first (or pick a new name) if you need to replace one.
"""
import click

from flexiv.pdk.config_header_pb2 import ConfigHeader
from flexiv.pdk.config_service_pb2 import ConfigType, SaveConfigRequest
from flexiv.pdk.scene.target_waypoint_pb2 import TargetWaypoint
from flexiv.pdk.spatial.waypoint_pb2 import CartesianWaypoint, JointWaypoint

from .._common import check, open_client, rpc, se3
from .._config_resource import config_group


def _parse_joints(text):
    """Parse a comma/space-separated string of joint positions into floats."""
    if not text:
        return []
    return [float(tok) for tok in text.replace(",", " ").split()]


def _format_system_pose(pose):
    """Render a TargetWaypoint for `system-pose get` -> (json-dict, text lines)."""
    p = pose.cartesian.pose
    data = {
        "name": pose.header.name,
        "parent": pose.header.parent,
        "position": [p.position.x, p.position.y, p.position.z],
        "quaternion": [p.rotation.x, p.rotation.y, p.rotation.z, p.rotation.w],
        "joints": list(pose.joint.position),
    }
    lines = [
        f"System pose: {data['name']} (parent {data['parent']})",
        f"Position:   {data['position']}",
        f"Quaternion: {data['quaternion']}",
        f"Joints:     {data['joints']}",
    ]
    return data, lines


system_pose_group = config_group(
    "system-pose", ConfigType.CONFIG_TYPE_SYSTEM_POSE,
    help="Create, list, and remove full-state system poses (requires an active workcell).",
    label="system poses", json_key="system_poses",
    get_field="system_pose", formatter=_format_system_pose,
)


@system_pose_group.command("create")
@click.argument("name")
@click.option("--parent", default="world", show_default=True,
              help="System/frame this pose belongs to.")
@click.option("--pos", nargs=3, type=float, default=(0.0, 0.0, 0.0),
              help="Cartesian position x y z (m).")
@click.option("--quat", nargs=4, type=float, default=(0.0, 0.0, 0.0, 1.0),
              help="Cartesian orientation quaternion x y z w.")
@click.option("--joints", default="",
              help="Joint positions, comma- or space-separated (e.g. '0,0.5,-0.3,1.2,0,0.8,0').")
@click.pass_context
@rpc
def system_pose_create(ctx, name, parent, pos, quat, joints):
    """Create system pose NAME from a Cartesian pose and its joint positions."""
    joint_positions = _parse_joints(joints)
    pose = TargetWaypoint(
        header=ConfigHeader(name=name, parent=parent),
        cartesian=CartesianWaypoint(pose=se3(pos, quat)),
        joint=JointWaypoint(position=joint_positions),
    )
    with open_client(ctx) as client:
        check(client.config.stub.Save(SaveConfigRequest(system_pose=pose)), "Create system pose")
    click.echo(f"Created system pose {name!r} on {parent!r} "
               f"({len(joint_positions)} joint positions).")
