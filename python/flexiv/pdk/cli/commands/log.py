"""``log`` command: the server's recent log, or follow it as it is written.

Needs no active workcell. When a call fails, the log usually shows why.
"""
import click
import grpc

from flexiv.pdk.common.log_entry_pb2 import LogEntry
from flexiv.pdk.common.log_service_pb2 import (
    GetLogHistoryRequest,
    StreamLogEntriesRequest,
)

from .._common import check, open_client, rpc

_LEVELS = ["debug", "info", "warning", "error"]


def _format(entry):
    time = entry.timestamp.ToDatetime().strftime("%H:%M:%S.%f")[:-3]
    level = LogEntry.Level.Name(entry.level)
    return f"[{time}][{level}][{entry.source}] {entry.message}"


@click.command("log")
@click.option("--level", type=click.Choice(_LEVELS), default="debug", show_default=True,
              help="Lowest level to show.")
@click.option("--count", type=int, default=50, show_default=True,
              help="Newest entries to show. 0 shows everything the server kept.")
@click.option("--follow", "-f", is_flag=True,
              help="Keep printing new entries until interrupted.")
@click.pass_context
@rpc
def log_cmd(ctx, level, count, follow):
    """Print the server's recent log entries, oldest first."""
    min_level = LogEntry.Level.Value(level.upper())
    with open_client(ctx) as client:
        history = check(client.log.stub.GetLogHistory(GetLogHistoryRequest(
            min_level=min_level, max_entries=count)), "Get log")
        for entry in history.entries:
            click.echo(_format(entry))
        if not follow:
            return
        try:
            for entry in client.log.stub.StreamLogEntries(
                    StreamLogEntriesRequest(min_level=min_level)):
                click.echo(_format(entry))
        except KeyboardInterrupt:
            pass
        except grpc.RpcError as error:
            if error.code() != grpc.StatusCode.CANCELLED:
                raise
