"""Per-resource command groups for the ``pdk-scene`` CLI.

Each module here exposes one click Group (or Command) that is registered lazily
in :data:`flexiv.pdk.cli.main.LAZY_COMMANDS`. Modules import their own proto
stubs so that only the invoked command pays that import cost.
"""
