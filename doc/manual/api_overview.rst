API Overview
============

The ``Client`` is the entry point to the SDK. It owns one gRPC channel to the
server and creates a *service client* for each gRPC service the first time you
use it. Each service client exposes a ``stub`` on which you call RPCs.

.. code-block:: text

   client.<service>.stub.<Rpc>(request)          # Python
   client.<service>().stub-><Rpc>(&ctx, req, &res);  // C++

Python
------

.. code-block:: python

   from flexiv.pdk import Client

   client = Client(target="localhost:50052")   # default target
   try:
       ...
   finally:
       client.close()

   # or, preferably, as a context manager:
   with Client("192.168.1.100:50052") as client:
       ...

* ``Client(target: str = "localhost:50052")`` creates an **insecure** gRPC
  channel to ``target``. No network traffic happens until the first RPC.
* Service attributes are created lazily and cached.
* ``client.channel`` is the underlying ``grpc.Channel``; you can use it to make
  stubs for any service yourself.
* ``client.check_version()`` asks the server whether this client works with
  it and returns ``(compatible, message)``. ``compatible`` is False when the
  server cannot be reached. See :doc:`/environment_compatibility`.
* ``client.license.install_file(path)`` installs a ``.lic`` file. See
  :doc:`/activate_licenses`.
* ``close()`` closes the channel. Exiting the ``with`` block calls it for you.

C++
---

.. code-block:: cpp

   #include <flexiv/pdk/client.hpp>

   flexiv::pdk::Client client("localhost:50052");        // insecure channel
   // or bring your own channel (TLS, custom arguments, ...):
   flexiv::pdk::Client client2(grpc::CreateChannel(target, creds));

* ``Client`` is neither copyable nor movable. Share it with
  ``std::shared_ptr<Client>`` when several components need it.
* Accessors such as ``client.workcell()`` return a reference to a
  ``ServiceClient<ServiceT>`` whose public member ``stub`` is the generated
  ``ServiceT::Stub``. Accessors are thread-safe.
* ``channel()`` returns the shared ``grpc::Channel``.
* ``client.license().InstallFile(path, &response)`` installs a ``.lic`` file.
  See :doc:`/activate_licenses`.
* ``CheckVersion(&message)`` returns whether this client works with the server;
  *message* says why not, or gives the server version.
* ``close()`` releases the channel. Any accessor called afterwards throws
  ``std::runtime_error("PDK client channel is closed")``. Do not keep using
  service client references or stubs obtained before ``close()``.
* gRPC requires a fresh ``grpc::ClientContext`` for every call.

Session (C++)
~~~~~~~~~~~~~

``flexiv::pdk::Session`` (``<flexiv/pdk/session.hpp>``) bundles a
``std::shared_ptr<Client>`` with a ``watch::Subscriber`` so that GUI editors and
viewers can share one handle for both RPCs and streamed events:

.. code-block:: cpp

   auto client = std::make_shared<flexiv::pdk::Client>();
   flexiv::pdk::Session session(client);

   session.client()->frame().stub->...;                       // RPCs
   auto sub = session.watch().Subscribe<SceneEvent>(...);     // events

The Session must outlive everything it is passed to. Destroying it stops every
subscription it handed out. ``client()`` may be null when the Session was built
without a client (for example, offline tests).

Service map
-----------

The table maps each ``Client`` member to its gRPC service. Services marked
*licensed* need a license on the server machine (:doc:`activate_licenses`).

Services marked *no workcell needed* work without an active workcell. Every
other service acts on the scene of the active workcell, so create or load one
first (:doc:`/workcells`). ``ConfigService`` rejects every call without one with
``FAILED_PRECONDITION``; the others report the missing workcell or item in
``status``.

.. list-table::
   :header-rows: 1
   :widths: 22 22 40 16

   * - Python attribute
     - C++ accessor
     - gRPC service
     - Notes
   * - ``workcell``
     - ``workcell()``
     - ``flexiv.pdk.workcell.WorkcellService``
     - no workcell needed
   * - ``config``
     - ``config()``
     - ``flexiv.pdk.ConfigService``
     -
   * - ``frame``
     - ``frame()``
     - ``flexiv.pdk.FrameService``
     -
   * - ``scene_event``
     - ``scene_event()``
     - ``flexiv.pdk.SceneEventService``
     - streaming
   * - ``collision``
     - ``collision()``
     - ``flexiv.pdk.scene.collision.CollisionService``
     -
   * - ``system``
     - ``system()``
     - ``flexiv.pdk.system.SystemService``
     -
   * - ``system_config``
     - ``system_config()``
     - ``flexiv.pdk.system.ComponentsService``
     -
   * - ``system_state``
     - ``system_state()``
     - ``flexiv.pdk.system.StateService``
     -
   * - ``kinematics``
     - ``kinematics()``
     - ``flexiv.pdk.system.KinematicsService``
     -
   * - ``point_to_point_path``
     - ``point_to_point_path()``
     - ``flexiv.pdk.point_to_point_path.PointToPointPathService``
     - licensed
   * - ``surface_finish``
     - ``surface_finish()``
     - ``flexiv.pdk.surface_finish.generator.SurfaceFinishService``
     - licensed
   * - ``mesh_operation``
     - ``mesh_operation()``
     - ``flexiv.pdk.MeshOperationService``
     - licensed
   * - ``camera``
     - ``camera()``
     - ``flexiv.pdk.camera.CameraService``
     -
   * - ``reconstruction``
     - ``reconstruction()``
     - ``flexiv.pdk.scene.reconstruction.ReconstructionService``
     -
   * - ``license``
     - ``license()``
     - ``flexiv.pdk.license.LicenseService``
     - no workcell needed
   * - ``version``
     - ``version()``
     - ``flexiv.pdk.common.VersionService``
     - no workcell needed
   * - ``log``
     - ``log()``
     - ``flexiv.pdk.common.LogService``
     - streaming; no workcell needed

Finding message types
---------------------

Request and response messages live in the module generated from the service's
``.proto`` file. The Python module path mirrors the proto path, with ``_pb2``
appended (``_pb2_grpc`` for stubs):

.. list-table::
   :header-rows: 1

   * - Proto file
     - Python module
     - C++ header
   * - ``flexiv/pdk/workcell/workcell_service.proto``
     - ``flexiv.pdk.workcell.workcell_service_pb2``
     - ``flexiv/pdk/workcell/workcell_service.pb.h`` (stub in
       ``workcell_service.grpc.pb.h``)
   * - ``flexiv/pdk/scene/object.proto``
     - ``flexiv.pdk.scene.object_pb2``
     - ``flexiv/pdk/scene/object.pb.h``

The C++ namespace follows the proto ``package``, for example
``flexiv::pdk::workcell::CreateRequest``; see :doc:`/cpp_api` for the two
services whose package differs from their folder. See :doc:`/services` for the
full list.
