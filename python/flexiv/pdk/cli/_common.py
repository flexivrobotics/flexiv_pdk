"""Shared helpers for the ``pdk-scene`` CLI command modules.

These are imported by every module under :mod:`flexiv.pdk.cli.commands`.
Keep this module light: importing it must not pull in per-resource proto stubs,
so that the lazy top-level group (see :mod:`flexiv.pdk.cli.main`) stays fast.
"""
import functools

import click
import grpc

from flexiv.pdk import Client
from flexiv.pdk.spatial.geometry_pb2 import Quaternion, SE3Pose, Vector3

DEFAULT_TARGET = "localhost:50052"


def se3(pos, quat):
    """Build an SE3Pose from a position 3-tuple and an (x, y, z, w) quaternion."""
    px, py, pz = pos
    qx, qy, qz, qw = quat
    return SE3Pose(
        position=Vector3(x=px, y=py, z=pz),
        rotation=Quaternion(x=qx, y=qy, z=qz, w=qw),
    )


def check(response, context):
    """Raise a click error if a response carries a non-zero status code."""
    status = getattr(response, "status", None)
    code = getattr(status, "code", 0) if status is not None else 0
    if code != 0:
        message = getattr(status, "message", "")
        raise click.ClickException(f"{context} failed: {message} (code {code})")
    return response


def open_client(ctx):
    """Open a Client against the target stored on the root context."""
    return Client(ctx.obj["target"])


def rpc(func):
    """Turn a raw grpc.RpcError (e.g. server unreachable) into a clean click error."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except grpc.RpcError as error:
            code = error.code().name if error.code() is not None else "UNKNOWN"
            raise click.ClickException(f"gRPC {code}: {error.details()}")
    return wrapper
