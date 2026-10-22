Activate Licenses
=================

Most services are free. Three services need a per-feature license:

.. list-table::
   :header-rows: 1

   * - Client attribute
     - gRPC service
     - License code
   * - ``client.point_to_point_path``
     - ``PointToPointPathService``
     - ``point_to_point_path``
   * - ``client.surface_finish``
     - ``SurfaceFinishService``
     - ``surface_finish``
   * - ``client.mesh_operation``
     - ``MeshOperationService``
     - ``mesh_operation``

How licenses work
-----------------

* A license is bound to the **TPM 2.0 security chip** of the computer running the
  server. It cannot be copied to another machine. Enable the chip before you
  start the server; see :doc:`/install_server`.
* Licenses are checked locally; no network connection is needed at run time.
* Installing a license **takes effect immediately**. No restart is needed.
* A machine without a license still runs every other service normally.

Calling an unlicensed service
-----------------------------

The call returns normally with ``status.code == 5`` (``PERMISSION_DENIED``).
``status.message`` names the service and says what to do. Nothing is raised,
so the standard status check (:doc:`error_handling`) catches it.

Checking license state
----------------------

``LicenseService`` does not need an active workcell:

.. code-block:: python

   from flexiv.pdk.license.license_service_pb2 import ListRequest

   res = client.license.stub.List(ListRequest())
   for service in res.services:
       print(service.display_name, service.state, service.detail)
   print("TPM available:", res.tpm_available, res.tpm_detail)

Each ``ServiceLicense`` has a ``state``:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - ``LicenseState``
     - Meaning
   * - ``LICENSE_STATE_LICENSED``
     - Licensed and usable.
   * - ``LICENSE_STATE_NO_LICENSE``
     - No license installed for this service.
   * - ``LICENSE_STATE_EXPIRED``
     - The license has expired.
   * - ``LICENSE_STATE_WRONG_MACHINE``
     - The license was issued for another computer.
   * - ``LICENSE_STATE_INVALID_LICENSE``
     - The license failed verification.
   * - ``LICENSE_STATE_UNSUPPORTED_FORMAT``
     - The license needs a newer PDK.
   * - ``LICENSE_STATE_SERVER_TOO_OLD``
     - The license needs a newer PDK server.
   * - ``LICENSE_STATE_TPM_UNAVAILABLE``
     - The security chip could not be read.

Buying and installing a license
-------------------------------

Licensing moves two files.

1. **Get this computer's identifier** and email it to Flexiv:

   .. code-block:: bash

      pdk-scene license identifier             # writes license_identifier.txt

   From code: ``client.license.stub.GetDeviceIdentifier(GetDeviceIdentifierRequest())``
   returns ``identifier``. It is a single line of about 2.4 kB, so send it as a
   file rather than pasting it.

2. **Install the ``.lic`` file** Flexiv sends back:

   .. code-block:: bash

      pdk-scene license install -f NEB-2026-0042.lic

   or from Python:

   .. code-block:: python

      from flexiv.pdk.license.license_service_pb2 import LicensedService

      response = client.license.install_file("NEB-2026-0042.lic")
      if response.status.code != 0:
          print(response.status.message)
      else:
          print("Newly licensed:", [LicensedService.Name(s) for s in response.newly_licensed])

   or from C++:

   .. code-block:: cpp

      flexiv::pdk::license::SaveResponse response;
      const grpc::Status status = client.license().InstallFile("NEB-2026-0042.lic", &response);
      if (status.ok() && response.status().code() != flexiv::pdk::common::Status::OK) {
        std::cerr << response.status().message() << std::endl;
      }

   ``install_file`` and ``InstallFile`` read the file **on the client machine**
   and send its contents over gRPC, so the server may be on another host or in a
   container.

3. **Verify**:

   .. code-block:: bash

      pdk-scene license status

   .. code-block:: text

      Security chip: TPM 2.0 INTC
      Licenses in:   /home/flexiv/user_data/license

      SERVICE              LICENSE  EXPIRES     DETAIL
      Point-to-point path  yes      2028-01-31  licensed to My Company
      Surface finish       yes      2028-01-31  licensed to My Company
      Mesh operations      no       -

      License NEB-2026-0042 for My Company, expires 2028-01-31

   ``DETAIL`` says why a service is not licensed, such as an expired license or
   an unreadable security chip. ``--json`` prints one object per service.
