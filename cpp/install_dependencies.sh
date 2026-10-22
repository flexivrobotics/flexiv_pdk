#!/bin/bash

# Define a wrapper to use sudo only if available
SUDO() {
    if command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        "$@"
    fi
}

# Update and install dependencies
SUDO apt-get update
SUDO apt-get install -y libeigen3-dev libgrpc++-dev protobuf-compiler-grpc
