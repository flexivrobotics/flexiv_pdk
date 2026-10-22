#!/bin/bash

this_script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
flexiv_pdk_path="`cd "${this_script_path}/../../..";pwd`"
echo "flexiv_pdk_path = $flexiv_pdk_path"

# get access to let the GUI in docker work properly
xhost +local:*

# docker run the official ros humble desktop container
docker run -it \
  --name ros_jazzy_container \
  --network=host \
  --device=/dev/dri:/dev/dri \
  --env LOCAL_UID=$(id -u "$USER") -e LOCAL_GID=$(id -g "$USER") \
  --volume /dev/shm:/dev/shm -e DISPLAY=$DISPLAY \
  --volume /tmp/.X11-unix/:/tmp/.X11-unix/ \
  --volume $flexiv_pdk_path:/home/ros2_ws/src/flexiv_pdk \
  osrf/ros:jazzy-desktop bash
