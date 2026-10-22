Flexiv PDK Server
=================

The PDK server runs in Docker. Start it before running any PDK client.

System Requirements
-------------------

* Ubuntu 22.04, x86_64
* [Docker Engine apt package](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository)
* [Docker Group](https://docs.docker.com/engine/install/linux-postinstall/)
* About 21 GB of free disk: 14 GB for the Docker image, and 7 GB for its download while it is pulled

Advanced services - point-to-point path, surface finish and mesh operations -
are licensed, and a license is tied to the TPM 2.0 security chip in the
computer running the server. Basic services need no chip and no license.

* TPM 2.0, enabled in the BIOS/UEFI setup. Look for "TPM", "Security Device",
  "Intel PTT" or "AMD fTPM"; most machines built since 2016 have one.

Check it before you start:

    ls -l /dev/tpmrm0

If that file exists, the chip is enabled and the server can use it. If it is
missing, the server still runs - the licensed services simply stay switched off,
and the server says so when it starts.

The server optionally uses an NVIDIA GPU for faster motion planning:

* [NVIDIA Driver](https://documentation.ubuntu.com/server/how-to/graphics/install-nvidia-drivers/index.html)
* [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

Set Up
------

From this folder, run once per release:

    bash setup_server.sh

Add `--gpu` to use the GPU. The script pulls the server image that `IMAGE` names
by its digest, so Docker accepts no other image, then starts the server's
container. Run with `--help` for the other options.

Your workcells and licenses are kept in `flexiv_pdk_data/`, beside the
flexiv_pdk repository folder. Every release uses that folder, so keep it when
you upgrade.

If the pull is interrupted, run the script again: Docker keeps the layers it has
already downloaded.

Run
---

    bash run_server.sh

This opens terminal tabs for the planning servers, so it needs a desktop
session. The server listens on port 50052. It starts the container again if the
computer was restarted since setup.

Stop the server with Ctrl+C, then stop its container:

    bash docker_stop.sh

Upgrade
-------

Check out the new release of the flexiv_pdk repository, then run
`bash setup_server.sh` from this folder again. Your workcells and licenses in
`flexiv_pdk_data/` are kept. Use a client of the same release.

Remove the images of older releases to free disk:

    docker image ls ghcr.io/flexivrobotics/flexiv_pdk_server
    docker image rm ghcr.io/flexivrobotics/flexiv_pdk_server:<old version>

Troubleshooting
---------------

See [doc/TROUBLESHOOTING.md](doc/TROUBLESHOOTING.md).
