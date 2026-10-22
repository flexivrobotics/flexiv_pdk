"""``pdk-scene`` — a thin CLI over :class:`flexiv.pdk.Client`.

It drives the WorkcellService, ConfigService, SceneEventService and friends on a
running PDK server. See ``examples/python/scene_example.py`` for the
equivalent programmatic API.

A Workcell must be active before any resource command (``object``,
``surface-path``, ...): run ``pdk-scene workcell load <name>`` (or ``create``,
which loads by default) first, otherwise the server rejects ConfigService RPCs
with FAILED_PRECONDITION. ``license``, ``log`` and ``version`` are the
exceptions: they need no workcell.

Examples::

    pdk-scene workcell create demo
    pdk-scene object create widget --box 0.1 0.1 0.1 --pos 0.3 0 0.2 --color 1 0 0 1
    pdk-scene object move widget --pos 0.5 0.1 0.3
    pdk-scene object list
    pdk-scene surface-path create weld --parent part_left --from 0 0 0 --to 0.1 0 0
    pdk-scene surface-path list
    pdk-scene watch                      # stream scene events (debug)
    pdk-scene license status             # which features are licensed
    pdk-scene log --level warning        # the server's recent warnings and errors
    pdk-scene version                    # client and server versions

Structure
---------
Each resource lives in its own module under ``flexiv.pdk.cli.commands`` and is
registered lazily below: the top-level ``--help`` and every invocation import
only the one module (and its proto stubs) that is actually used. Adding a
resource is a new small file plus one line in ``LAZY_COMMANDS``.
"""
import importlib

import click

from ._common import DEFAULT_TARGET

# name -> "module.path:attribute" of the click Group/Command implementing it.
# Kept as strings so nothing is imported until the command is actually run.
LAZY_COMMANDS = {
    "workcell":    "flexiv.pdk.cli.commands.workcell:workcell",
    "object":      "flexiv.pdk.cli.commands.object:object_group",
    "camera":      "flexiv.pdk.cli.commands.camera:camera_group",
    "coordinate":  "flexiv.pdk.cli.commands.coordinate:coordinate_group",
    "surface-path": "flexiv.pdk.cli.commands.surface_path:surface_path_group",
    "system-pose": "flexiv.pdk.cli.commands.system_pose:system_pose_group",
    "watch":       "flexiv.pdk.cli.commands.watch:watch_cmd",
    "system":      "flexiv.pdk.cli.commands.system:system_group",
    "license":     "flexiv.pdk.cli.commands.license:license_group",
    "log":         "flexiv.pdk.cli.commands.log:log_cmd",
    "version":     "flexiv.pdk.cli.commands.version:version_cmd",
}


class LazyGroup(click.Group):
    """A click.Group whose subcommands are imported on first use.

    Subcommands are declared as ``{name: "module:attr"}`` import paths; the
    module is only imported when that subcommand is listed for help or invoked.
    """

    def __init__(self, *args, lazy=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._lazy = dict(lazy or {})

    def list_commands(self, ctx):
        return sorted(set(super().list_commands(ctx)) | set(self._lazy))

    def get_command(self, ctx, name):
        target = self._lazy.get(name)
        if target is not None:
            module_path, attr = target.split(":")
            return getattr(importlib.import_module(module_path), attr)
        return super().get_command(ctx, name)


@click.group(cls=LazyGroup, lazy=LAZY_COMMANDS)
@click.option("--target", default=DEFAULT_TARGET, show_default=True,
              help="PDK server address (host:port).")
@click.pass_context
def pdk_scene(ctx, target):
    """Inspect and modify the PDK scene on a running SDK server."""
    ctx.ensure_object(dict)
    ctx.obj["target"] = target


if __name__ == "__main__":
    pdk_scene()
