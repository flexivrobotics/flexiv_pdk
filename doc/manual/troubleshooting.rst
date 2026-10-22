Troubleshooting
===============

First, read the server's log. A response's ``status.message`` says why that
call failed; the log shows what led up to it, including warnings from calls
that succeeded:

.. code-block:: bash

   pdk-scene log --level warning

From code, use ``LogService.GetLogHistory``. Neither needs a workcell.

gRPC ``UNAVAILABLE`` / connection refused
   The server is not running or not reachable. Check the address (default
   ``localhost:50052``), firewalls, and that the server container is up. Use
   ``pdk-scene --target HOST:PORT version`` as a quick connectivity test: it
   also checks that the client and server versions work together. Starting the
   server is covered in :doc:`/install_server`.

gRPC ``INTERNAL`` with no details
   The client's generated stubs do not match the server's ``.proto`` files.
   The server cannot parse the request and fails before the handler runs, so it
   looks like a server bug. If you installed from source, regenerate the stubs
   (``bash python/generate_protos.sh``) after every pull. With a wheel, install
   the version that matches the server; ``pdk-scene version`` checks it.

``FAILED_PRECONDITION`` (code 4) from scene calls
   No workcell is active. Call ``WorkcellService.Create`` and ``Load`` once
   before scene calls. See :doc:`/workcells`.

``PERMISSION_DENIED`` (code 5)
   The service is licensed and this machine has no valid license for it. Run
   ``pdk-scene license status`` and see :doc:`/activate_licenses`.

A call "succeeds" but nothing happens
   The operation failed at application level. Check ``response.status.code``
   and ``status.message``; failures are not raised. See
   :doc:`/error_handling`.

Objects or tool frames appear rotated or collapsed
   A quaternion was left unset (all zeros). Set ``w=1.0`` for the identity on
   every pose, ``Visual.origin`` and ``Collision.origin``.

Mesh objects do not load
   ``Mesh.filename`` is resolved **on the server**. Use a path the server can
   read (for a containerized server, the path inside the container; see
   :doc:`/install_server`), and set ``scale`` to ``(1, 1, 1)``.

IK or planning fails immediately
   ``KinematicsService.ComputeIK`` and ``PointToPointPathService.Plan`` need the
   name of a saved collision configuration. Save one first
   (:doc:`/collision`).

Surface-finish results disappeared
   Redoing a stage clears the results of later stages. Re-run
   ``RefinePath`` and ``CreateRobotMotion`` after regenerating the nominal path.

CMake: Protobuf version mismatch
   ``flexiv_pdk`` requires the Protobuf *major.minor* version it was built
   against. Use your Ubuntu release's packaged Protobuf
   (``libprotobuf-dev``) and the matching ``flexiv_pdk`` platform build.

CMake: ``flexiv_pdk`` not found
   Pass ``-DCMAKE_PREFIX_PATH=<install prefix>`` (not ``CMAKE_INSTALL_PREFIX``)
   or ``-Dflexiv_pdk_DIR=<prefix>/lib/cmake/flexiv_pdk``.

C++: ``PDK client channel is closed``
   A service accessor was called after ``Client::close()``.
