Error Handling
==============

A PDK call can fail at two different layers, and you must check both.

1. **Transport errors** (gRPC status). The server is unreachable, the call timed
   out, the request could not be parsed, and so on. In Python these raise
   ``grpc.RpcError``; in C++ the returned ``grpc::Status`` is not ``ok()``.
2. **Application errors** (``response.status``). The server received the request
   but could not do what you asked: the object does not exist, no workcell is
   loaded, the service is not licensed. **Nothing is raised.** The response
   comes back normally, with a non-zero ``status.code``.

.. warning::

   A response object always exists after a successful gRPC call, even when the
   operation failed. Always check ``status.code``.

The ``Status`` message
----------------------

Most responses contain ``flexiv.pdk.common.Status status = 1``:

.. list-table::
   :header-rows: 1
   :widths: 10 28 62

   * - Code
     - Name
     - Meaning
   * - 0
     - ``OK``
     - Success.
   * - 1
     - ``NOT_FOUND``
     - The named item does not exist.
   * - 2
     - ``INVALID_ARGUMENT``
     - The request is malformed or a value is out of range.
   * - 3
     - ``INTERNAL_ERROR``
     - The server failed while executing the request.
   * - 4
     - ``FAILED_PRECONDITION``
     - Preconditions are not met. Most often: no workcell is loaded.
   * - 5
     - ``PERMISSION_DENIED``
     - The service needs a license this computer does not have.

``status.message`` is optional and, when present, explains the failure in plain
language.

Recommended pattern
-------------------


Python:

.. code-block:: python

   import grpc
   from flexiv.pdk.workcell.workcell_service_pb2 import NameRequest

   class PdkError(RuntimeError):
       pass

   def check(response, what: str):
       """Raises if a PDK response carries a failure status."""
       status = getattr(response, "status", None)
       if status is not None and status.code != 0:
           raise PdkError(f"{what} failed: {status.message} (code {status.code})")
       return response

   try:
       res = check(client.workcell.stub.Load(NameRequest(name="demo")), "Load workcell")
   except grpc.RpcError as e:
       print(f"gRPC {e.code().name}: {e.details()}")
   except PdkError as e:
       print(e)

C++:

.. code-block:: cpp

   bool ProtoStatusOk(const flexiv::pdk::common::Status& status)
   {
     return status.code() == flexiv::pdk::common::Status::OK;
   }

   grpc::ClientContext ctx;
   flexiv::pdk::workcell::NameRequest req;
   req.set_name("demo");
   flexiv::pdk::workcell::WorkcellResponse res;
   const grpc::Status s = client.workcell().stub->Load(&ctx, req, &res);
   if (!s.ok()) {
     std::cerr << "gRPC error: " << s.error_message() << "\n";
   } else if (!ProtoStatusOk(res.status())) {
     std::cerr << "Load failed: " << res.status().message() << "\n";
   }

Exceptions to the pattern
-------------------------

* Some ``ReconstructionService`` and ``CameraService`` RPCs return a bare
  ``common.Status`` instead of a response wrapper. Check ``.code`` on the
  returned message itself.

Common failures
---------------

``FAILED_PRECONDITION`` from scene calls
   No workcell is active. Create or load one first (:doc:`workcells`).

``PERMISSION_DENIED``
   The service is licensed and this machine has no valid license for it. See
   :doc:`activate_licenses`.

gRPC ``UNAVAILABLE``
   The server is not running or not reachable at the target address.

gRPC ``INTERNAL`` with no details
   Usually stale generated stubs in a source install. See :doc:`/troubleshooting`.
