#!/bin/bash
# Absolute path of this script
this_script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
parent_path="$( dirname "$this_script_path" )"
echo "$parent_path" > /tmp/flexiv_nebula_sdk_server_path.txt

source $this_script_path/scripts/container_util.sh
start_server_container || exit 1

source $this_script_path/scripts/server_terminal_util.sh
kill_docker_exec_scripts

# Launch new gnome-terminal for planning server and save its PID
gnome-terminal --title="Planning Server" --tab --active -- bash -c "bash '$this_script_path/scripts/run_planning_server.sh'"
save_docker_exec_script_pid "run_planning_server.sh"

# Launch new gnome-terminal for scanplan server and save its PID
gnome-terminal --title="ScanPlan Server" --tab --active -- bash -c "bash '$this_script_path/scripts/run_scanplan_server.sh'"
save_docker_exec_script_pid "run_scanplan_server.sh"

# Launch new gnome-terminal for reconstruction server and save its PID
gnome-terminal --title="Reconstruction Server" --tab --active -- bash -c "bash '$this_script_path/scripts/run_reconstruction_server.sh'"
save_docker_exec_script_pid "run_reconstruction_server.sh"

# Launch new gnome-terminal for vamp server and save its PID
#gnome-terminal --title="Vamp Planning Server" --tab --active -- bash -c "bash '$this_script_path/scripts/run_vamp_server.sh'"
#save_docker_exec_script_pid "run_vamp_server.sh"

# Run Flexiv Nebula
docker exec --user flexiv -it $FLEXIV_NEBULA_CONTAINER_NAME bash /home/flexiv/release/flexiv_nebula_server/run_server.sh

kill_docker_exec_scripts
