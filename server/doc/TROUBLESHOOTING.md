Troubleshooting 
===============

1. Flexiv Nebula does not launch, and terminal shows error mentioning `qt.qpa.plugin` and `xcb`, for example:

        qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "/home/flexiv/release/flexiv_nebula/plugins" even though it was found

    Fix: Remove the docker container, re-run the container, then re-run Flexiv Nebula.

        docker container ls
        docker container rm <CONTAINER ID of flexiv nebula>
        docker_run.sh

2. docker_run.sh has error related to `nvidia-container-cli`, for example:

        docker: Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: error running prestart hook
        nvidia-container-cli: initialization error: load library failed: libnvidia-ml.so.1: cannot open shared object file: no such file or directory: unknown.

    Fix:

        sudo apt-get install --reinstall nvidia-container-toolkit
        sudo apt-get install --reinstall docker-ce

3. No Space Left on Device

    Docker images can take up significant disk space. 
    Before upgrading the Flexiv Nebula version, we recommend removing all existing Flexiv Nebula images.
    This process can also be used to uninstall and reinstall Flexiv Nebula.

    1. Check Docker disk usage and existing images:

            docker system df
            docker image list

    2. Stop any Flexiv Nebula containers using `docker_stop.sh`
    3. Remove Flexiv Nebula Docker images, for example:

            docker image rm flexivrobot/flexiv_nebula:v2.1_base_customer

        Alternatively, you can remove all Docker images on the computer, even those unrelated to Flexiv Nebula. Review the Docker image list and verify that all can be safely deleted.

            docker system prune -a
