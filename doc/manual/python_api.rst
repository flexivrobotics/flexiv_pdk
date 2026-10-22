Python API
==========

Hand-written reference for the Python modules of the ``flexivpdk`` package.
Generated message and stub modules are described in :doc:`services` and
:doc:`messages`.

.. py:module:: flexiv.pdk

flexiv.pdk
----------

.. py:data:: __version__

   Package version string, for example ``"1.0.0"``.

.. py:class:: Client(target: str = "localhost:50052")

   Main entry point. Creates an insecure gRPC channel to *target* and exposes
   one lazily created service client per gRPC service. Each service client has
   a ``stub`` attribute, the generated gRPC stub.

   Usable as a context manager; the channel is closed on exit.

   .. py:attribute:: channel
      :type: grpc.Channel

      The underlying channel.

   .. py:method:: check_version() -> tuple[bool, str]

      Ask the server whether this client works with it: same major and minor
      version. Returns ``(compatible, message)``; *message* says why not, or
      gives the server version. Returns ``(False, message)`` when the server
      cannot be reached; *message* says why.

   .. py:method:: close() -> None

      Close the channel.

   .. py:property:: workcell
   .. py:property:: config
   .. py:property:: frame
   .. py:property:: scene_event
   .. py:property:: collision
   .. py:property:: system
   .. py:property:: system_config
   .. py:property:: system_state
   .. py:property:: kinematics
   .. py:property:: point_to_point_path
   .. py:property:: surface_finish
   .. py:property:: mesh_operation
   .. py:property:: camera
   .. py:property:: reconstruction
   .. py:property:: version
   .. py:property:: log

      Service clients. See :doc:`/api_overview` for the service each one
      wraps.

   .. py:property:: license
      :type: flexiv.pdk.client.LicenseServiceClient

      License service client, with a helper for installing license files.

.. py:currentmodule:: flexiv.pdk.client

.. py:class:: LicenseServiceClient

   Returned by :py:attr:`flexiv.pdk.Client.license`. Not exported from
   ``flexiv.pdk``; import it from ``flexiv.pdk.client`` if you need the type.

   .. py:attribute:: stub

      ``LicenseServiceStub``.

   .. py:method:: install_file(path, file_name: str = "")

      Install the ``.lic`` file Flexiv sent back. Takes effect immediately.

      The file is read on this machine and its contents sent over gRPC, so the
      server may run on another host or in a container.

      :param path: Path to the ``.lic`` file.
      :param file_name: Name to save it as on the server. Defaults to the
         file's own name, or the license id where that name is not plain
         (only ``A-Z a-z 0-9 - _ .``).
      :returns: ``SaveResponse``. Check ``status.code``; an unverifiable license
         is reported there, not raised.
      :raises OSError: The file cannot be read.
      :raises ValueError: The file is empty.

.. py:module:: flexiv.pdk.watch

flexiv.pdk.watch
----------------

Consume server-streaming ("watch") RPCs with automatic reconnection. See
:doc:`/scene_events`.

.. py:data:: Executor

   ``Callable[[Callable[[], None]], None]``: given ``fn``, runs ``fn()`` on the
   thread of your choice. The Python form of C++ ``watch::Executor``.

.. py:class:: Options(executor=None, reconnect=True, backoff_initial_s=0.5, backoff_max_s=10.0, backoff_factor=2.0, max_retries=-1)

   Dataclass controlling delivery and reconnection.

   :param executor: ``Callable[[Callable[[], None]], None]`` that runs a
      callback on the thread of your choice. ``None`` delivers on the watch's
      background thread.
   :param reconnect: Reconnect when the stream ends or fails, including when
      the server cancels it.
   :param backoff_initial_s: First reconnect delay, in seconds.
   :param backoff_max_s: Maximum reconnect delay.
   :param backoff_factor: Multiplier applied after each failed attempt. The
      delay resets after an event is received.
   :param max_retries: Maximum consecutive reconnects; ``-1`` for unlimited.

.. py:function:: watch(open_stream, options=None) -> Iterator

   Blocking generator that yields stream events and reconnects with backoff.
   Stop by breaking out of the loop or closing the generator; either cancels
   the live call. ``Options.executor`` is ignored.

   :param open_stream: Zero-argument callable that opens the stream, for
      example ``lambda: client.scene_event.stub.WatchSceneEvents(request)``.
      Called again on every reconnect.

.. py:class:: Subscriber()

   Opens watch RPCs as background subscriptions. Usable as a context manager
   (calls :py:meth:`stop_all` on exit).

   .. py:method:: subscribe(open_stream, on_event, options=None) -> Subscription

      Start a background subscription. *on_event* is called with each event.
      Keep the returned :py:class:`Subscription` and close it to stop.

   .. py:method:: subscribe_rpc(stub_method, request, on_event, options=None) -> Subscription

      Shorthand for ``subscribe(lambda: stub_method(request), on_event, options)``.

   .. py:method:: stop_all() -> None

      Close every subscription created by this subscriber.

.. py:class:: Subscription(open_stream, on_event, options=None)

   Handle to an active watch. The constructor starts the stream at once on a
   daemon thread named ``pdk-watch``; :py:meth:`Subscriber.subscribe` calls it
   for you. Usable as a context manager.

   .. py:property:: active
      :type: bool

      True while the watch is running.

   .. py:method:: close(timeout=None) -> None

      Stop the stream and join the worker thread. Idempotent and safe from any
      thread; when called from inside the callback, the join is skipped.

Exceptions raised by a callback are logged on the ``flexiv.pdk.watch`` logger
and the stream continues.

.. py:module:: flexiv.pdk.spatial

flexiv.pdk.spatial
------------------

.. py:function:: to_numpy(message) -> numpy.ndarray

   ``Vector3`` → ``[x, y, z]``; ``Quaternion`` → ``[w, x, y, z]``;
   ``SE3Pose`` → 4×4 homogeneous matrix; ``JointWaypoint`` →
   ``(position, velocity)``; a ``repeated double`` field, list or tuple → 1-D
   ``float64`` array. Raises ``TypeError`` for anything else.

   An all-zero (unset) ``Quaternion``, alone or in an ``SE3Pose``, reads as the
   identity rotation. The server may not treat it so; always set ``w=1`` in
   messages you send.

.. py:function:: to_proto(value, target=None)

   ``target`` is ``Vector3`` (``[x, y, z]``), ``Quaternion`` (``[w, x, y, z]``
   or a ``Rotation``), ``SE3Pose`` (4×4), ``JointWaypoint`` (a
   ``(position, velocity)`` pair) or ``list`` (``repeated double``). It may be
   omitted only for a 4×4 matrix or a ``Rotation``. Raises ``TypeError`` for a
   missing or unknown ``target``, and ``ValueError`` for the wrong shape. See
   :doc:`/math_conversions`.

.. py:module:: flexiv.pdk.physics

flexiv.pdk.physics
------------------

.. py:function:: to_numpy(message) -> numpy.ndarray
   :no-index:

   ``Inertia`` → its symmetric 3×3 inertia tensor. Raises ``TypeError`` for
   anything else.

.. py:function:: to_proto(value, target=None)
   :no-index:

   A 3×3 matrix → ``Inertia``, from the upper triangle. ``target`` may be
   ``Inertia`` or omitted. Raises ``ValueError`` for another shape. See
   :doc:`/math_conversions`.

.. py:module:: flexiv.pdk.license.license_file

flexiv.pdk.license.license_file
-------------------------------

Helpers behind :py:meth:`flexiv.pdk.client.LicenseServiceClient.install_file`.

.. py:function:: read_license_file(path) -> str

   Read a license file (raw or base64 form) and return the base64 text for
   ``SaveRequest.license``.

.. py:function:: license_text(raw: bytes) -> str

   Return base64 for either form of license file. Whitespace in base64 input is
   ignored; already-encoded input is passed through.

.. py:function:: server_file_name(path) -> str

   The file's own name if the server accepts it as a plain name, otherwise
   ``""`` (the server then names the file after the license id).

Command-line entry point
------------------------

``pdk-scene`` is the console script ``flexiv.pdk.cli.main:pdk_scene``. See
:doc:`/pdk_scene_cli`.
