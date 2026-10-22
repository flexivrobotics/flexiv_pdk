"""``system`` commands: the joint positions of a system in the scene.

``joints get`` / ``joints set``. These move the system in the scene, not a real
or simulated robot, and are not saved: a system starts at the home position in
its config. Requires an active workcell.
"""
import json

import click

from flexiv.pdk.system.components.joint_group_pb2 import JointGroup
from flexiv.pdk.system.state_service_pb2 import (
    GetJointPositionRequest,
    SetJointPositionRequest,
)

from .._common import check, open_client, rpc

_GROUPS = {
    "system": JointGroup.JOINT_GROUP_SYSTEM,
    "arm": JointGroup.JOINT_GROUP_ARM,
    "external-robot-axis": JointGroup.JOINT_GROUP_EXTERNAL_ROBOT_AXIS,
    "external-workpiece-axis": JointGroup.JOINT_GROUP_EXTERNAL_WORKPIECE_AXIS,
}

_group_option = click.option(
    "--group", type=click.Choice(list(_GROUPS)), default="system", show_default=True,
    help="Joint group.")


@click.group("system")
def system_group():
    """Joint positions of a system in the scene (requires an active workcell)."""


@system_group.group("joints")
def joints_group():
    """Get or set the joint positions of a system in the scene."""


@joints_group.command("get")
@click.argument("name")
@_group_option
@click.option("--json", "as_json", is_flag=True, help="Print as JSON.")
@click.pass_context
@rpc
def joints_get(ctx, name, group, as_json):
    """Print the joint positions of system NAME, in rad or m."""
    with open_client(ctx) as client:
        response = check(client.system_state.stub.GetJointPosition(GetJointPositionRequest(
            system_name=name, joint_group=_GROUPS[group])), "Get joint positions")
    positions = list(response.joint_position)
    if as_json:
        click.echo(json.dumps({"system": name, "group": group, "joint_position": positions}))
    else:
        click.echo(" ".join(f"{value:.6f}" for value in positions))


# ignore_unknown_options lets negative positions such as -0.7 through as values.
@joints_group.command("set", context_settings={"ignore_unknown_options": True})
@click.argument("name")
@click.argument("positions", nargs=-1, type=float, required=True)
@_group_option
@click.pass_context
@rpc
def joints_set(ctx, name, positions, group):
    """Move system NAME in the scene to POSITIONS, one per joint, in rad or m."""
    with open_client(ctx) as client:
        check(client.system_state.stub.SetJointPosition(SetJointPositionRequest(
            system_name=name, joint_group=_GROUPS[group], joint_position=positions)),
            "Set joint positions")
    click.echo(f"Moved system {name!r}.")
