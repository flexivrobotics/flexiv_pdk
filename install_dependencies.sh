#!/bin/bash

# Define a wrapper to use sudo only if available
SUDO() {
    if command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        "$@"
    fi
}

# Update and install dependencies. gRPC's CMake config on Ubuntu 24.04 and later needs
# grpc_cpp_plugin, from protobuf-compiler-grpc, even though the SDK is prebuilt.
SUDO apt-get update
SUDO apt-get install -y cmake pkg-config libeigen3-dev libprotobuf-dev libgrpc++-dev protobuf-compiler-grpc
