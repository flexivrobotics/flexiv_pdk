Workcells
=========

A **workcell** is a named, persistent project on the server. It holds the whole
scene: robot systems, objects, cameras, coordinate frames, collision
configurations, saved poses and generated paths.

At most one workcell is **active** at a time. There is none until you create
or load one, and removing the active workcell leaves none active. Scene
services operate on the active workcell.

.. important::

   ``ConfigService`` (and the scene services that build on it) require an
   active workcell. Without one, calls fail with ``FAILED_PRECONDITION``
   (code 4): *"Cannot execute ConfigService RPC. No active Workcell is loaded.
   Create or load a Workcell first."*

   You only need to create or load a workcell **once** per server session;
   afterwards make as many scene calls as you like.

   ``WorkcellService`` itself, ``LicenseService``, ``LogService`` and
   ``VersionService`` do not need an active workcell.

Lifecycle
---------

``WorkcellService`` (``client.workcell``) provides:

.. list-table::
   :header-rows: 1
   :widths: 22 30 48

   * - RPC
     - Request
     - Effect
   * - ``Create``
     - ``CreateRequest(name, description)``
     - Create a new, empty workcell.
   * - ``Load``
     - ``NameRequest(name)``
     - Make the workcell active. Returns the ``Workcell``.
   * - ``GetActive``
     - ``Empty``
     - Return the active ``Workcell``.
   * - ``List``
     - ``Empty``
     - Return every ``Workcell`` (name, description, created/updated timestamps).
   * - ``Exists``
     - ``NameRequest(name)``
     - ``exists`` is true if the workcell exists.
   * - ``Rename``
     - ``RenameRequest(old_name, new_name)``
     -
   * - ``SetDescription``
     - ``SetDescriptionRequest(name, description)``
     -
   * - ``Remove``
     - ``NameRequest(name)``
     - Delete a workcell and everything in it.

Typical startup
---------------

The examples start from a clean workcell every time. Removing first makes the
script re-runnable. A missing workcell is reported as ``NOT_FOUND`` in
``res.status.code``, not as a ``grpc.RpcError``:

.. code-block:: python

   from flexiv.pdk.common.status_pb2 import Status
   from flexiv.pdk.workcell.workcell_service_pb2 import CreateRequest, NameRequest

   name = "example_workcell"
   res = client.workcell.stub.Remove(NameRequest(name=name))
   if res.status.code not in (Status.OK, Status.NOT_FOUND):
       raise RuntimeError(f"Remove failed: {res.status.message}")
   res = client.workcell.stub.Create(CreateRequest(name=name, description="demo"))
   if res.status.code != Status.OK:
       raise RuntimeError(f"Create failed: {res.status.message}")
   res = client.workcell.stub.Load(NameRequest(name=name))
   if res.status.code != Status.OK:
       raise RuntimeError(f"Load failed: {res.status.message}")

``Create`` fails with ``INVALID_ARGUMENT`` if the workcell already exists.
See :doc:`error_handling`.

To keep existing work instead, load it only if it exists:

.. code-block:: python

   if client.workcell.stub.Exists(NameRequest(name=name)).exists:
       client.workcell.stub.Load(NameRequest(name=name))
   else:
       client.workcell.stub.Create(CreateRequest(name=name))
       client.workcell.stub.Load(NameRequest(name=name))

Checking readiness
------------------

``ConfigService.CheckReady(CheckReadyRequest(type=...))`` asks the server
whether the preconditions for a config type are met. ``status.code == OK``
means ready; ``FAILED_PRECONDITION`` means not ready, with an explanation in
``status.message``.

From the command line
---------------------

.. code-block:: bash

   pdk-scene workcell create demo        # creates and loads
   pdk-scene workcell load demo
   pdk-scene workcell list               # active workcell is marked with '*'
