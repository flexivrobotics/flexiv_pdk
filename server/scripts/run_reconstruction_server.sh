#!/bin/bash
# Absolute path of this script
this_script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

FLEXIV_NEBULA_CONTAINER_NAME="${FLEXIV_NEBULA_CONTAINER_NAME:-flexiv_nebula}"

# save the gnome-terminal tab pid to a file, so it can be closed later
source $this_script_path/server_terminal_util.sh

if docker inspect --format="{{ .State.Running }}" $FLEXIV_NEBULA_CONTAINER_NAME 2> /dev/null; then
  docker exec --user flexiv -it $FLEXIV_NEBULA_CONTAINER_NAME bash /home/flexiv/release/planning_server/run_reconstruction_server.sh
else
  echo "Container not running, Please run 'bash docker_run.sh' first"
fi
