"""``watch`` command: stream scene events (debug aid)."""
import click
import grpc

from flexiv.pdk.scene_event_service_pb2 import WatchSceneEventsRequest

from .._common import open_client, rpc


@click.command("watch")
@click.pass_context
@rpc
def watch_cmd(ctx):
    """Stream scene events until interrupted (debug aid)."""
    from flexiv.pdk.watch import watch as watch_stream

    with open_client(ctx) as client:
        request = WatchSceneEventsRequest()  # empty filters => all origins/types
        click.echo("Watching scene events (Ctrl-C to stop)...")
        try:
            for event in watch_stream(
                    lambda: client.scene_event.stub.WatchSceneEvents(request)):
                entity = (f"{event.entity.type}:{event.entity.name!r}"
                          if event.HasField("entity") else "-")
                click.echo(
                    f"change={event.change} origin={event.origin} "
                    f"entity={entity} frames={list(event.frames)}")
        except KeyboardInterrupt:
            click.echo("Stopped.")
        except grpc.RpcError as error:
            raise click.ClickException(f"WatchSceneEvents failed: {error}")
