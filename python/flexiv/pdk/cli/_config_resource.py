"""Factory for ConfigService-backed resource command groups.

Most scene resources (object, camera, coordinate, surface-path, system, and the
pose types) share the exact same ``list`` / ``get`` / ``remove`` shape against
``ConfigService`` — they differ only by ``ConfigType`` and, for ``get``, which
oneof field of the response holds the message. :func:`config_group` generates
those three verbs so each resource module only writes its resource-specific
``create`` (and any extra verbs, e.g. ``object move``).

Usage::

    grp = config_group(
        "object", ConfigType.CONFIG_TYPE_OBJECT,
        help="Create, move, inspect, and remove scene objects ...",
        label="objects", json_key="objects",
        get_field="object", formatter=_format_object,
    )

    @grp.command("create")
    ...
"""
import json

import click
from google.protobuf.json_format import MessageToDict

from flexiv.pdk.config_service_pb2 import ListConfigRequest, TypeNameConfigRequest

from ._common import check, open_client, rpc


def config_group(name, config_type, help, *,
                 label=None, json_key=None, get_field=None, formatter=None):
    """Build a click.Group with generic ``list`` / ``get`` / ``remove`` verbs.

    Parameters
    ----------
    name : str
        Command-group name, e.g. ``"object"`` or ``"surface-path"``.
    config_type : ConfigType
        The ``CONFIG_TYPE_*`` enum value this resource maps to.
    help : str
        Group help text (the one-line summary shown by the parent ``--help``).
    label : str, optional
        Human plural used in messages (defaults to ``name``).
    json_key : str, optional
        Top-level key for ``list --json`` output (defaults to ``name``).
    get_field : str, optional
        Attribute of ``GetConfigResponse`` holding the config message. If not
        given, ``get`` dumps the whole response.
    formatter : callable, optional
        ``msg -> (data_dict, text_lines)`` used by ``get`` to render the config.
        ``text_lines`` may be ``None`` to fall back to pretty-printed JSON.
    """
    label = label or name
    json_key = json_key or name

    grp = click.Group(name=name, help=help)

    @grp.command("list", help=f"List all {label} in the active workcell.")
    @click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
    @click.pass_context
    @rpc
    def list_cmd(ctx, as_json):
        with open_client(ctx) as client:
            resp = check(client.config.stub.List(
                ListConfigRequest(type=config_type)), f"List {label}")
        names = list(resp.names)
        if as_json:
            click.echo(json.dumps({json_key: names}))
            return
        if not names:
            click.echo(f"Scene has no {label}.")
            return
        for n in names:
            click.echo(n)

    @grp.command("get", help=f"Show {name} CFG_NAME.")
    @click.argument("cfg_name")
    @click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
    @click.pass_context
    @rpc
    def get_cmd(ctx, cfg_name, as_json):
        with open_client(ctx) as client:
            resp = check(client.config.stub.Get(TypeNameConfigRequest(
                type=config_type, name=cfg_name)), f"Get {name}")
        msg = getattr(resp, get_field) if get_field else resp
        if formatter:
            data, lines = formatter(msg)
        else:
            data, lines = MessageToDict(msg), None
        if as_json:
            click.echo(json.dumps(data))
            return
        if lines is None:
            click.echo(json.dumps(data, indent=2))
        else:
            for line in lines:
                click.echo(line)

    @grp.command("remove", help=f"Remove {name} CFG_NAME from the scene.")
    @click.argument("cfg_name")
    @click.pass_context
    @rpc
    def remove_cmd(ctx, cfg_name):
        with open_client(ctx) as client:
            check(client.config.stub.Remove(TypeNameConfigRequest(
                type=config_type, name=cfg_name)), f"Remove {name}")
        click.echo(f"Removed {name} {cfg_name!r}.")

    return grp
