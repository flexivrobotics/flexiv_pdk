#!/bin/bash
# Creates the PDK server container from the settings setup_server.sh saved.
#
# Source this file, then use:
#     start_server_container    # create and start the container, if it is not running

FLEXIV_NEBULA_CONTAINER_NAME="${FLEXIV_NEBULA_CONTAINER_NAME:-flexiv_nebula}"

container_util_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
server_config_file="$(dirname "$container_util_path")/.server.conf"
# Workcells and licenses: flexiv_pdk_data/, beside the flexiv_pdk repository
server_data_dir="$(cd "$container_util_path/../../.." && pwd)/flexiv_pdk_data"

source "$container_util_path/gpu_util.sh"
source "$container_util_path/tpm_util.sh"

# Returns 0 if the container is running.
server_container_running() {
  [[ "$(docker inspect --format='{{ .State.Running }}' "$FLEXIV_NEBULA_CONTAINER_NAME" 2> /dev/null)" == "true" ]]
}

start_server_container() {
  if server_container_running; then
    return 0
  fi
  if [[ ! -f "$server_config_file" ]]; then
    echo "Container '$FLEXIV_NEBULA_CONTAINER_NAME' is not running, and the server is not set up."
    echo "Run 'bash setup_server.sh' first."
    return 1
  fi

  # SERVER_IMAGE and SERVER_ENABLE_GPU
  source "$server_config_file"

  if ! docker image inspect "$SERVER_IMAGE" > /dev/null 2>&1; then
    echo "Docker image $SERVER_IMAGE is not loaded. Run 'bash setup_server.sh' again."
    return 1
  fi

  local gpu_option tpm_option
  get_gpu_docker_option "$SERVER_ENABLE_GPU" gpu_option
  get_tpm_docker_option tpm_option

  mkdir -p "$server_data_dir/user_data/extensions/lib" \
           "$server_data_dir/user_data/extensions/xml" \
           "$server_data_dir/user_data/license" \
           "$server_data_dir/workcell"

  # A stopped container of the same name blocks the new one
  docker rm "$FLEXIV_NEBULA_CONTAINER_NAME" > /dev/null 2>&1 || true

  if [[ -n "${DISPLAY:-}" ]]; then
    xhost +local:* > /dev/null 2>&1 || true
  fi

  echo "Starting container '$FLEXIV_NEBULA_CONTAINER_NAME' from $SERVER_IMAGE"
  # shellcheck disable=SC2086
  docker run -it \
    $gpu_option \
    $tpm_option \
    --network=host \
    --name="$FLEXIV_NEBULA_CONTAINER_NAME" \
    --device=/dev/dri:/dev/dri \
    --volume /dev/shm:/dev/shm -e DISPLAY="${DISPLAY:-}" \
    --volume /tmp/.X11-unix/:/tmp/.X11-unix/ \
    --volume "$server_data_dir/workcell":/home/flexiv/workcell \
    --volume "$server_data_dir/user_data":/home/flexiv/user_data \
    --env LOCAL_UID="$(id -u)" -e LOCAL_GID="$(id -g)" \
    --workdir=/home/flexiv/release \
    --detach \
    --rm \
    "$SERVER_IMAGE" > /dev/null

  # The entrypoint gives the container user this user's id, re-owning its home; wait for it
  echo "Preparing the container for user id $(id -u). This takes up to a minute."
  local waited=0
  until [[ "$(docker exec "$FLEXIV_NEBULA_CONTAINER_NAME" stat -c %u /home/flexiv 2> /dev/null)" == "$(id -u)" ]] &&
        ! docker exec "$FLEXIV_NEBULA_CONTAINER_NAME" pgrep -x 'usermod|groupmod' > /dev/null 2>&1; do
    if ! server_container_running || (( waited >= 300 )); then
      echo "Container '$FLEXIV_NEBULA_CONTAINER_NAME' did not finish starting. See: docker logs $FLEXIV_NEBULA_CONTAINER_NAME"
      return 1
    fi
    sleep 2
    waited=$((waited + 2))
  done

  # let the container user read the TPM, for the license check
  grant_container_tpm_access "$FLEXIV_NEBULA_CONTAINER_NAME"

  echo "Container '$FLEXIV_NEBULA_CONTAINER_NAME' is running."
}
