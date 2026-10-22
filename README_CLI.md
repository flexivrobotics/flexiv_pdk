# Flexiv PDK CLI (`pdk-scene`)

`pdk-scene` lets you inspect and modify a Flexiv PDK scene from your
terminal, without writing any code. It talks to a running PDK server over the
same gRPC interface the language bindings use, so anything you create with it —
workcells, objects, cameras, paths — is immediately visible to your C++,
TypeScript, or Python application, and vice versa.

The tool is implemented in Python and ships with the Python package, but you
never write or import Python to use it. Use this CLI for one-off, interactive work,
and use the SDK for real logic — loops, computed waypoints, reacting to an
event stream, or integrating several services together.

## Install

The `pdk-scene` command comes with the Flexiv PDK Python package. Install it
as [python/README.md](python/README.md) describes, then confirm the command is
available:

```bash
pdk-scene --help
```

## How the commands are organized

Commands follow a `noun verb` shape, like `git` or `kubectl`: you name a resource
(`workcell`, `object`, `camera`, `coordinate`, `surface-path`, `system-pose`, `system`)
and an action to take on it. Most resources share the same `create`, `list`,
`get`, and `remove` verbs, so once you know one you can guess the rest. Help is
available at every level:

```bash
pdk-scene --help                    # the resource groups
pdk-scene object --help             # the verbs for one resource
pdk-scene object create --help      # the options for one command
```

Read commands (`list`, `get`) also accept `--json`, which is handy when you want
to pipe output into `jq` or a script.

Every command exits non-zero when something goes wrong, and reports the failure
as a readable `Error:` message on stderr — a rejected request, or a server that
cannot be reached — so mistakes surface properly in scripts and CI.

## Before you start

A PDK server must be running. By default the CLI connects to
`localhost:50052`; point it elsewhere with the global `--target` option, which
goes before the subcommand:

```bash
pdk-scene --target 192.168.1.50:50052 workcell list
```

Almost every command operates on the **active workcell**, so nearly every session
begins by creating or loading one.

## Workflow: set up a workcell

Create a new workcell (this also loads it), or load an existing one. The active
workcell is marked with a `*` in the list:

```bash
pdk-scene workcell create demo          # creates and loads "demo"
pdk-scene workcell load demo            # or load an existing one
pdk-scene workcell list
```

If you skip this step, the scene commands below fail with a
`FAILED_PRECONDITION` error telling you no workcell is loaded — load one and
retry.

## Workflow: add and inspect scene objects

Add a simple box or a mesh, then read it back. Poses are given as `--pos x y z`
in meters relative to a parent frame (defaulting to `world`), with orientation
`--quat x y z w` defaulting to identity:

```bash
# A 10 cm box at (0.3, 0, 0.2) in the world frame
pdk-scene object create widget --box 0.1 0.1 0.1 --pos 0.3 0 0.2

# The same box in red: --color R G B A, each from 0 to 1
pdk-scene object create marker --box 0.1 0.1 0.1 --color 1 0 0 1

# A mesh parented to another object (the path must be visible to the server)
pdk-scene object create bracket --mesh /server/path/bracket.stl --parent widget

pdk-scene object list                   # names in the active workcell
pdk-scene object get widget             # pose and shapes, human-readable
pdk-scene object get widget --json      # the same data as JSON
```

Objects can be moved and removed after creation:

```bash
pdk-scene object move widget --pos 0.5 0.1 0.3
pdk-scene object remove bracket
```

## Workflow: add other scene content

Cameras, coordinate frames, and full-state system poses follow the same pattern —
a `create` with the resource's own options, plus the shared `list` / `get` /
`remove`:

```bash
# A camera with a view frustum, parented to an object
pdk-scene camera create cam0 --parent widget --camera-id 0 \
    --far-width 1.2 --far-height 0.9 --far-distance 2.0 --near-distance 0.1

# A named coordinate frame, like a URDF link
pdk-scene coordinate create fixture --pos 0.4 0 0.1

# A full-state robot pose: a Cartesian pose plus the joints that realize it
pdk-scene system-pose create home --pos 0.4 0 0.3 \
    --joints "0, 0.5, -0.3, 1.2, 0, 0.8, 0"

pdk-scene camera list
pdk-scene coordinate get fixture
pdk-scene system-pose remove home
```

The server refuses to overwrite an existing system pose, so `remove` it first (or
choose a new name) if you need to replace one.

## Workflow: add a surface-finish path

A surface-finish path is a sequence of Cartesian waypoints attached to a parent
object and expressed in that object's frame. The `create` command builds a
straight line between two points; `--points` controls how many waypoints are
sampled along it (default 2):

```bash
# A 2-point line, 10 cm along +X from the object's origin
pdk-scene surface-path create weld --parent widget --from 0 0 0 --to 0.1 0 0

# 5 waypoints along a diagonal
pdk-scene surface-path create scan --parent widget \
    --from 0 0 0 --to 0.15 0 0.05 --points 5

pdk-scene surface-path get weld          # parent plus interpolated waypoints
```

`--parent` is required, since the waypoints are interpreted in that object's
frame.

## Workflow: check and install a service license

Basic services are free. Advanced ones need a license - point-to-point path,
surface finish and mesh operations - tied to the security chip (TPM) in
the computer running the server, so it works offline and cannot be copied to
another machine. Unlike every other command here, `license` needs no workcell.

```bash
pdk-scene license identifier               # writes the file to email to Flexiv
pdk-scene license install -f NEB-1234.lic  # takes effect at once, no restart
```

Both steps move files. An identifier is a single line of about 2.4 kB and a
license is binary, so neither survives being retyped: attach the file Flexiv
asks for, and install the `.lic` file Flexiv sends back. `-o` writes the
identifier somewhere other than `license_identifier.txt`.

`pdk-scene license status` shows where things stand:

```
SERVICE              LICENSE  EXPIRES     DETAIL
Point-to-point path  yes      2028-01-31  licensed to My Company
Surface finish       yes      never       licensed to My Company
Mesh operations      no       -
```

`DETAIL` explains a license failure, like the license has expired or a security chip cannot be read.

`--json` prints the same thing machine-readably — one object per service with
`licensed`, `expires` and `license_id` — for a health check or a scripted
pre-flight test.

## Workflow: move a system in the scene

A system starts at the home position saved in its config. To try out other
joint positions — before planning, or to check for collisions — move it in the
scene. This does not move a real or simulated robot, which you drive with the
Flexiv RDK, and it is not saved:

```bash
pdk-scene system joints get system_1                        # every actuated joint, rad or m
pdk-scene system joints get system_1 --group arm --json
pdk-scene system joints set system_1 0 -0.7 0 1.57 0 0.7 0 --group arm
```

## Workflow: check versions and read the server log

A client works with a server of the same major and minor version. `version`
prints both and fails when they do not match:

```bash
pdk-scene version
```

When a command fails, the server's log usually says why. It holds what the
server did, warnings about calls that still succeeded, and its background work:

```bash
pdk-scene log                       # the newest 50 entries
pdk-scene log --level warning       # only warnings and errors
pdk-scene log --follow              # keep printing new entries until Ctrl-C
```

Neither command needs a workcell.

## Workflow: watch live scene events

To see changes as they happen — useful when debugging the server or another
client — stream events until you press Ctrl-C:

```bash
pdk-scene watch
```

Each line reports the change, its origin, the affected entity, and the frames
involved.

## Related docs

- Repository overview and all language bindings: [README.md](README.md)
- Python library usage: [python/README.md](python/README.md)
- Runnable example scripts (the programmatic equivalents of these commands):
  [examples/python/README.md](examples/python/README.md)
