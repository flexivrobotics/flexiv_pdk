#!/usr/bin/env bash
set -e

# Move to SDK root to access the 'proto' folder alongside 'python'
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

# The grpcio-tools version sets the minimum grpcio/protobuf the generated stubs accept.
# Raise the grpcio and protobuf floors in pyproject.toml together with this pin;
# build_wheel.sh fails if they fall behind.
GRPCIO_TOOLS_VERSION="1.84.0"

echo "Installing grpcio-tools==${GRPCIO_TOOLS_VERSION} in the current environment..."
pip install "grpcio-tools==${GRPCIO_TOOLS_VERSION}"

echo "Generating Python Protobuf/gRPC stubs..."
proto_files=$(find proto -name "*.proto")
python3 -m grpc_tools.protoc -Iproto \
    --python_out=python \
    --grpc_python_out=python \
    $proto_files

echo "Protobuf stubs generated successfully inside python/flexiv/pdk/!"
