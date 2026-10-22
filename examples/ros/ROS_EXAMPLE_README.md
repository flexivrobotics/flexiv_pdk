# ROS EXAMPLE

flexiv_pdk can be built as a stand-alone library using cmake, or built in a ROS workspace as a ROS package. To use the sdk with ROS: Download, clone, or submodule flexiv_pdk into your ROS workspace.

This example uses a ROS docker container, so you can try it, without installing ROS.


## Setup ROS2 Docker Container

Docker Setup
Installing ROS2 can be quite a hassle due to the installation size and there may be conflicts with other libraries that our repositories use. Instead, we can use ROS2 docker images.

1. One-time docker setup. Install [docker engine](https://docs.docker.com/engine/install/ubuntu/).
2. In a terminal, pull the ROS2 docker image by running:

        docker pull osrf/ros:jazzy-desktop

3. Create a docker container, such that:

    * container name is “ros_jazzy_container”
    * container maps the flexiv_nebaul_sdk repo on host computer into the docker container's ros workspace

    In the NON-CONTAINER terminal, run:

        cd /my-path-to/flexiv_pdk/example/ros
        bash scripts/docker_run_ros.sh

## Build

1. Install the dependencies for this ros package. In the CONTAINER terminal, run:

        cd /home/ros2_ws/
        source /opt/ros/jazzy/setup.bash
        apt update
        rosdep update
        rosdep install --from-paths src/flexiv_pdk --ignore-src -r -y

2. Build and install this ros package. In the CONTAINER terminal, run:

        cd /home/ros2_ws/
        source /opt/ros/jazzy/setup.bash
        colcon build --paths src/flexiv_pdk src/flexiv_pdk/examples/ros
        source install/setup.bash

3. Run the example application. In the CONTAINER terminal, run something like:


