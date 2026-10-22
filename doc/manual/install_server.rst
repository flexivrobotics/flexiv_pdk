Set Up the PDK Server
=====================

Every PDK client talks to a **PDK server**, which runs in Docker. Set up and
start the server before you install or run a client. The scripts are in the
``server/`` folder of the `PDK repository
<https://github.com/flexivrobotics/flexiv_pdk>`_.

.. note::

   Each release of the repository names exactly one server image. Use a client
   with the same major and minor version; see :doc:`/environment_compatibility`.

System requirements
-------------------

* Ubuntu 22.04, x86_64
* `Docker Engine apt package
  <https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository>`_
* Your user in the `docker group
  <https://docs.docker.com/engine/install/linux-postinstall/>`_
* About 21 GB of free disk: 14 GB for the Docker image, and 7 GB for its download
  while it is pulled
* A desktop session, as the server opens terminal tabs when it starts

The client does not have to run on the same computer. Any client that can reach
port 50052 of the server's computer can connect to it.

TPM 2.0 for licensed services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Point-to-point path, surface finish and mesh operations are licensed, and a
license is tied to the TPM 2.0 security chip of the computer running the server
(see :doc:`/activate_licenses`). The other services need no chip and no license.

Enable the TPM in the BIOS/UEFI setup. Look for "TPM", "Security Device",
"Intel PTT" or "AMD fTPM"; most computers built since 2016 have one. Then check
it:

.. code-block:: bash

   ls -l /dev/tpmrm0

If that file exists, the server can use the chip. If it is missing, the server
still runs, the licensed services stay switched off, and the server says so when
it starts.

GPU (optional)
~~~~~~~~~~~~~~

The server can use an NVIDIA GPU for faster motion planning. It needs:

* `NVIDIA driver
  <https://documentation.ubuntu.com/server/how-to/graphics/install-nvidia-drivers/index.html>`_
* `NVIDIA Container Toolkit
  <https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html>`_

Set up
------

From the root of the PDK repository, run once per release:

.. code-block:: bash

   bash server/setup_server.sh

The script pulls the server image that ``server/IMAGE`` names by its digest, so
Docker accepts no other image, and then starts the server's container. Options:

``--gpu``
   Use the NVIDIA GPU.
``--accept-eula``
   Accept the NVIDIA CUDA license without being asked. The image is derived from
   an NVIDIA CUDA image, so the script asks for it otherwise.

If the pull is interrupted, run the script again: Docker keeps the layers it has
already downloaded.

Your workcells and licenses are kept in ``flexiv_pdk_data/``, beside the PDK
repository folder. Every release uses that folder, so keep it when you upgrade.

Start and stop
--------------

Start the server:

.. code-block:: bash

   bash server/run_server.sh

It opens terminal tabs for the planning servers and listens on port 50052. If
the computer was restarted since setup, it starts the container again first.

Stop the server with Ctrl+C, then stop its container:

.. code-block:: bash

   bash server/docker_stop.sh

Check the connection
--------------------

With a client installed (:doc:`/install_for_python`), check that it reaches the
server and that their versions work together:

.. code-block:: bash

   pdk-scene version

It prints both versions and fails if their major or minor versions differ. To
check a server on another computer, add ``--target HOST:50052``. From code,
``VersionService.GetVersion`` gives the same answer; see :doc:`/services`.

Files on the server
-------------------

The server runs inside its container, so file paths it reads, such as
``Mesh.filename``, are paths **inside the container**. Two folders of
``flexiv_pdk_data/`` are shared with it:

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - On the server's computer
     - Inside the container
   * - ``flexiv_pdk_data/user_data``
     - ``/home/flexiv/user_data``
   * - ``flexiv_pdk_data/workcell``
     - ``/home/flexiv/workcell``

For example, a mesh copied to ``flexiv_pdk_data/user_data/meshes/part.obj`` is
loaded with ``/home/flexiv/user_data/meshes/part.obj``.

Upgrade
-------

Check out the new release of the PDK repository and run
``bash server/setup_server.sh`` again. Stop a running server first, as setup
will not replace a running container. Your workcells and licenses in
``flexiv_pdk_data/`` are kept. Upgrade the client to the same release.

Remove the images of older releases to free disk:

.. code-block:: bash

   docker image ls ghcr.io/flexivrobotics/flexiv_pdk_server
   docker image rm ghcr.io/flexivrobotics/flexiv_pdk_server:<old version>

Server problems
---------------

Setup says the container is running
   The server of an earlier setup is still up. Stop it with
   ``bash server/docker_stop.sh`` and run setup again.

The container did not finish starting
   Read why with ``docker logs flexiv_nebula``.

Licensed services are switched off
   Check that ``/dev/tpmrm0`` exists. If you enabled the TPM after the container
   started, stop the server and its container, then run
   ``bash server/run_server.sh`` again so the new container is given the chip.

For problems once the server is running, see :doc:`/troubleshooting`.
