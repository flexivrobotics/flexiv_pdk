"""``version`` command: client and server versions, and whether they work together.

Needs no active workcell.
"""
import click

from .._common import open_client, rpc


@click.command("version")
@click.pass_context
@rpc
def version_cmd(ctx):
    """Print the client and server versions, and fail if they do not work together."""
    from flexiv.pdk import __version__

    click.echo(f"Client version {__version__}")
    with open_client(ctx) as client:
        compatible, message = client.check_version()
    if not compatible:
        raise click.ClickException(message)
    click.echo(message)
