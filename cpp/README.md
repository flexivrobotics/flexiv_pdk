# Flexiv PDK [c++]

Use case: Robotic application that uses high-performance c++ libraries


## Supported Build System

Build System  | Support Level
------------- | ------------- 
Cmake         |	3.22+
ROS2 Colcon   |	Humble, Jazzy


## Build c++ cmake package

First, install required native dependencies (like gRPC and Protobuf):

    cd flexiv_pdk
    bash cpp/install_dependencies.sh

Then build and install the C++ SDK:

    cd cpp
    mkdir build && cd build
    cmake .. -DCMAKE_INSTALL_PREFIX=/my/local/install/path/
    make -j
    make install


## Build c++ ROS package

One time: Clone flexiv_pdk into the ros2 workspace and install its dependencies:

    cd ros2_ws/src
    git clone https://github.com/flexivrobotics/flexiv_pdk.git
    source /opt/ros/jazzy/setup.bash
    rosdep update
    rosdep install --from-paths flexiv_pdk --ignore-src -r -y
    
Build:

    cd ros2_ws
    source /opt/ros/jazzy/setup.bash
    colcon build
    source install/setup.bash
