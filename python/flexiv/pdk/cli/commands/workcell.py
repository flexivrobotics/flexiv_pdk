"""``workcell`` commands: create, load, and list workcells (WorkcellService)."""
import json

import click
import grpc
from google.protobuf import empty_pb2

from flexiv.pdk.workcell.workcell_service_pb2 import CreateRequest, NameRequest

from .._common import check, open_client, rpc


@click.group()
def workcell():
    """Create, load, and list workcells."""


@workcell.command("create")
@click.argument("name")
@click.option("--description", default="", help="Workcell description.")
@click.option("--load/--no-load", default=True,
              help="Load the workcell after creating it (default: load).")
@click.pass_context
@rpc
def workcell_create(ctx, name, description, load):
    """Create workcell NAME (and load it by default so `object` commands work)."""
    with open_client(ctx) as client:
        check(client.workcell.stub.Create(
            CreateRequest(name=name, description=description)), "Create workcell")
        if load:
            check(client.workcell.stub.Load(NameRequest(name=name)), "Load workcell")
    click.echo(f"Created workcell {name!r}" + (" and loaded it." if load else "."))


@workcell.command("load")
@click.argument("name")
@click.pass_context
@rpc
def workcell_load(ctx, name):
    """Load workcell NAME as the active workcell."""
    with open_client(ctx) as client:
        check(client.workcell.stub.Load(NameRequest(name=name)), "Load workcell")
    click.echo(f"Loaded workcell {name!r}.")


@workcell.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
@click.pass_context
@rpc
def workcell_list(ctx, as_json):
    """List all workcells; the active one is marked with '*'."""
    with open_client(ctx) as client:
        resp = check(client.workcell.stub.List(empty_pb2.Empty()), "List workcells")
        active = ""
        try:
            active = client.workcell.stub.GetActive(empty_pb2.Empty()).workcell.name
        except grpc.RpcError:
            pass
    names = [w.name for w in resp.workcells]
    if as_json:
        click.echo(json.dumps({"workcells": names, "active": active}))
        return
    if not names:
        click.echo("No workcells.")
        return
    for n in names:
        click.echo(f"{'* ' if n == active else '  '}{n}")
