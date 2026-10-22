Flexiv Nebula is built on and with the aid of the open source projects. Credits are given to these projects. The copyright notices and license texts can be viewed in the graphical user interface (GUI).


## Docker Image

Flexiv Nebula requires Ubuntu 22.04 with ROS2 Humble, Qt runtime libraries, NVIDIA CUDA Runtime, and other runtime dependencies. For convenience, we provide a Docker image that meets these requirements. Licenses can be found within the image. For example:

* /usr/share/doc/<package>/copyright
* /usr/share/common-licenses/<license>

This Docker image is derived from `nvidia/cuda:11.8.0-runtime-ubuntu22.04`, and governed by the [NVIDIA End User License Agreement (EULA)](https://docs.nvidia.com/cuda/eula/index.html). By using the image, you accept the terms and conditions of these licenses. Additional information my be found in the [nvidia/cuda docker website](https://hub.docker.com/r/nvidia/cuda). 

## GNU Lesser General Public License (LGPL) Notice

Flexiv Nebula ("Software") is built on and with the aid of libraries licensed under the GNU Lesser General Public License (LGPL) v2.0 and v3.1.

A user can install and execute a modified version of the Combined Work produced by recombining or relinking the Application with a modified version of the Linked Version. Flexiv may not provide support service, warranty, or updates for a work that has been modified or installed by the recipient, or for the User Product in which it has been modified or installed. 

### Installation Information for Qt5 Libraries

1. User loads and runs the flexiv_nebula Docker image
2. User removes the existing Qt5 libraries. For example:

    docker exec -it flexiv_nebula bash
    apt remove libQt5Widgets
    exit

3. User builds Qt5 shared libraries for Ubuntu 22.04, as specified in the Qt5 build instructions
4. User copies the shared libraries to Flexiv Nebula. For example:

    docker cp /path-on-host-computer/libQt5Widgets.so flexiv_nebula:/home/flexiv/release/flexiv_nebula/lib/libQt5Widgets.so


### Installation Information for Open CASCADE Technology

1. User loads and runs the flexiv_nebula Docker image
2. User removes the existing Open CASACADE Technology libraries. For example:

    docker exec --user flexiv -it flexiv_nebula bash
    cd ~/release/flexiv_nebula/lib
    rm libTKBRep.so*
    exit

3. User builds Open CASACADE Technology shared libraries for Ubuntu 22.04, as specified in the Open CASACADE Technology build instructions
4. User copies the shared libraries to Flexiv Nebula. For example:

    docker cp /path-on-host-computer/libTKBRep.so flexiv_nebula:/home/flexiv/release/flexiv_nebula/lib/libTKBRep.so


### Installation Information for Orocos KDL

1. User loads and runs the flexiv_nebula Docker image
2. User removes the existing Orocos KDL libraries libraries. For example:

    docker exec --user flexiv -it flexiv_nebula bash
    cd ~/release/flexiv_nebula/lib
    rm liborocos-kdl.so*
    exit

3. User builds Orocos KDL shared libraries for Ubuntu 22.04, as specified in the Orocos KDL build instructions
4. User copies the shared libraries to Flexiv Nebula. For example:

    docker cp /path-on-host-computer/liborocos-kdl.so flexiv_nebula:/home/flexiv/release/flexiv_nebula/lib/liborocos-kdl.so



