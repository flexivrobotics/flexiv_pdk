The ``pdk-scene`` Command-Line Tool
===================================

``pdk-scene`` inspects and modifies the scene on a running server from a
terminal, without writing code. It uses the same gRPC interface as every
binding, so it is useful whatever language your application is written in.
It is installed with the Python package; see :doc:`/install_for_python`.

Use it for one-off scene setup, inspection and debugging. It builds the
protobuf messages and checks status codes for you. Use the SDK for anything
with real logic.

Global options
--------------

.. code-block:: text

   pdk-scene [--target HOST:PORT] <group> <command> [options]

``--target``
   Server address. Default ``localhost:50052``. It goes **before** the group:

   .. code-block:: bash

      pdk-scene --target 192.168.1.50:50052 workcell list

``--help``
   Works at every level: ``pdk-scene --help``, ``pdk-scene object --help``,
   ``pdk-scene object create --help``.

``--json``
   Read commands can print JSON: ``workcell list``, every ``list`` and ``get``,
   ``system joints get`` and ``license status``.

On error, ``pdk-scene`` prints ``Error: gRPC <CODE>: <details>`` for transport
errors or ``Error: <action> failed: <message> (code N)`` for application errors,
and exits with a non-zero code.

.. important::

   Every command except ``workcell``, ``license``, ``log`` and ``version``
   needs an active workcell.

Command reference
-----------------

.. code-block:: text

   pdk-scene
   ├── workcell
   │   ├── create NAME [--description TEXT] [--load/--no-load]
   │   ├── load NAME
   │   └── list [--json]
   ├── object
   │   ├── create NAME [--parent world] [--pos X Y Z] [--quat X Y Z W]
   │   │               [--box LX LY LZ | --mesh PATH] [--color R G B A]
   │   ├── move NAME [--pos X Y Z] [--quat X Y Z W]
   │   ├── list [--json]
   │   ├── get NAME [--json]
   │   └── remove NAME
   ├── camera
   │   ├── create NAME [--parent world] [--pos] [--quat] [--camera-id 0]
   │   │               [--far-width 1.0] [--far-height 1.0]
   │   │               [--far-distance 2.0] [--near-distance 0.1]
   │   └── list | get | remove
   ├── coordinate
   │   ├── create NAME [--parent world] [--pos] [--quat] [--scale X Y Z]
   │   └── list | get | remove
   ├── surface-path
   │   ├── create NAME --parent OBJECT [--from X Y Z] [--to X Y Z]
   │   │               [--points N] [--quat X Y Z W]
   │   └── list | get | remove
   ├── system-pose
   │   ├── create NAME [--parent world] [--pos] [--quat] [--joints "j1,j2,..."]
   │   └── list | get | remove
   ├── system
   │   └── joints
   │       ├── get NAME [--group system] [--json]
   │       └── set NAME P1 P2 ... [--group system]
   ├── watch
   ├── license
   │   ├── status [--json]
   │   ├── identifier [-o FILE]
   │   └── install -f FILE.lic [--file-name NAME]
   ├── log [--level debug] [--count 50] [--follow]
   └── version

Defaults: ``--pos 0 0 0``, ``--quat 0 0 0 1`` (``x y z w``), ``--parent world``.

workcell
~~~~~~~~

.. code-block:: bash

   pdk-scene workcell create demo          # creates AND loads "demo" (use --no-load to skip)
   pdk-scene workcell load demo
   pdk-scene workcell list                 # the active workcell is marked with '*'

object
~~~~~~

.. code-block:: bash

   # A 10 cm box at (0.3, 0, 0.2) in the world frame
   pdk-scene object create widget --box 0.1 0.1 0.1 --pos 0.3 0 0.2
   # The same box in red: --color R G B A, each from 0 to 1
   pdk-scene object create marker --box 0.1 0.1 0.1 --color 1 0 0 1
   # A mesh parented to another object (the path must be readable by the server)
   pdk-scene object create bracket --mesh /server/path/bracket.stl --parent widget

   pdk-scene object list
   pdk-scene object get widget
   pdk-scene object get widget --json
   pdk-scene object move widget --pos 0.5 0.1 0.3   # persisted; emits CHANGE_UPDATED
   pdk-scene object remove bracket

``--box`` and ``--mesh`` are mutually exclusive, and ``--color`` needs one of
them. ``object move`` sets the whole pose in the parent frame: a ``--pos`` or
``--quat`` you leave out is reset to its default, not kept.

camera, coordinate, system-pose
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pdk-scene camera create cam0 --parent widget --camera-id 0 \
       --far-width 1.2 --far-height 0.9 --far-distance 2.0 --near-distance 0.1

   pdk-scene coordinate create fixture --pos 0.4 0 0.1

   # A full robot state: a Cartesian pose plus the joints that realize it
   pdk-scene system-pose create home --pos 0.4 0 0.3 \
       --joints "0, 0.5, -0.3, 1.2, 0, 0.8, 0"

   pdk-scene camera list
   pdk-scene coordinate get fixture
   pdk-scene system-pose remove home

The server refuses to overwrite an existing system pose; remove it first.

surface-path
~~~~~~~~~~~~

Creates a straight-line manual path on an object, interpolated with ``--points``
waypoints (at least 2):

.. code-block:: bash

   # 2 waypoints, 10 cm along +X from the object's origin
   pdk-scene surface-path create weld --parent widget --from 0 0 0 --to 0.1 0 0
   # 5 waypoints along a diagonal
   pdk-scene surface-path create scan --parent widget --from 0 0 0 --to 0.15 0 0.05 --points 5
   pdk-scene surface-path get weld

system
~~~~~~

Moves a system in the scene, to try joint positions before planning or to check
for collisions. It does not move a real or simulated robot, and it is not saved:
a system starts at the home position in its config. Positions are in rad or m.

.. code-block:: bash

   pdk-scene system joints get system_1                   # every actuated joint
   pdk-scene system joints get system_1 --group arm --json
   pdk-scene system joints set system_1 0 -0.7 0 1.57 0 0.7 0 --group arm

``--group`` is one of ``system``, ``arm``, ``external-robot-axis`` and
``external-workpiece-axis``.

watch
~~~~~

Streams scene events until interrupted; useful for debugging another client:

.. code-block:: text

   $ pdk-scene watch
   Watching scene events (Ctrl-C to stop)...
   change=1 origin=1 entity=4:'widget' frames=['widget']

Values are the enum numbers: ``change`` 1–5 are ADDED, UPDATED, REMOVED,
RENAMED, REFRESHED; ``origin`` 1 is CONFIG and 2 is FRAME; the entity type is a
``ConfigType`` (4 is OBJECT). See :doc:`/scene_events`.

license
~~~~~~~

Does not need a workcell. See :doc:`/activate_licenses`.

.. code-block:: bash

   pdk-scene license status                    # table of services and license state
   pdk-scene license identifier                # writes license_identifier.txt to email to Flexiv
   pdk-scene license install -f NEB-1234.lic   # takes effect at once, no restart

log and version
~~~~~~~~~~~~~~~

Neither needs a workcell. When a command fails, the server's log usually says
why:

.. code-block:: bash

   pdk-scene log                       # the newest 50 entries
   pdk-scene log --level warning       # only warnings and errors
   pdk-scene log --follow              # keep printing new entries until Ctrl-C
   pdk-scene version                   # client and server versions

``--count 0`` prints every entry the server kept. ``version`` fails when the
client and server major or minor versions differ.
