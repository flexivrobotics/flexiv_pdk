#!/bin/bash
# Pulls the PDK server Docker image this release names, then starts its container.
#
# Usage:
#     bash setup_server.sh [--gpu] [--accept-eula]
#
#     --gpu             use the NVIDIA GPU for faster motion planning
#     --accept-eula     accept the NVIDIA CUDA license without asking
#
# IMAGE names the image by its digest, so Docker refuses any other image. Workcells and
# licenses are kept in flexiv_pdk_data/, beside the flexiv_pdk repository.
set -euo pipefail

this_script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

enable_gpu=false
accept_eula=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --gpu) enable_gpu=true; shift ;;
    --accept-eula) accept_eula=true; shift ;;
    -h|--help) sed -n '2,11p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1. Run with --help." >&2; exit 1 ;;
  esac
done

source "$this_script_path/scripts/container_util.sh"

# IMAGE holds one line: <registry>/<name>:<version>@sha256:<digest>
reference="$(head -n 1 "$this_script_path/IMAGE")"
if [[ ! "$reference" =~ ^([^@:]+/[^@:]+):([^@:]+)@(sha256:[0-9a-f]{64})$ ]]; then
  echo "ERROR: $this_script_path/IMAGE does not name an image as <name>:<version>@sha256:<digest>." >&2
  exit 1
fi
name="${BASH_REMATCH[1]}"
version="${BASH_REMATCH[2]}"
image="$name@${BASH_REMATCH[3]}"
echo "PDK server v$version"

if [[ "$accept_eula" != true ]]; then
  echo "=============================="
  echo "         LICENSE AGREEMENT"
  echo "=============================="
  echo "This Docker image is derived from 'nvidia/cuda:11.8.0-runtime-ubuntu22.04', and"
  echo "governed by the NVIDIA End User License Agreement (https://docs.nvidia.com/cuda/eula/index.html)."
  echo "By using the CUDA images, you accept the terms and conditions of these licenses."
  echo ""
  read -r -p "Do you accept the license agreement? (yes/no): " response
  if [[ "$response" != "yes" ]]; then
    echo "You did not accept the license agreement. Exiting..."
    exit 1
  fi
fi

if server_container_running; then
  echo "Container '$FLEXIV_NEBULA_CONTAINER_NAME' is running. Run 'bash docker_stop.sh' first."
  exit 1
fi

if docker image inspect "$image" > /dev/null 2>&1; then
  echo "Docker image $name:$version is already here."
else
  echo "Pulling $name:$version. The first pull downloads several GB."
  docker pull "$image"
fi
docker tag "$image" "$name:$version"

cat > "$server_config_file" <<EOF
SERVER_IMAGE=$image
SERVER_ENABLE_GPU=$enable_gpu
EOF

start_server_container

echo ""
echo "Setup done. Workcells and licenses are kept in $server_data_dir."
echo "Start the server with: bash run_server.sh"
