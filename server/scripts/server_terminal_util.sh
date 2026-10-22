#!/bin/bash

# Save 
save_docker_exec_script_pid() {
    local script_name="$1"
    local this_script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
    local pid_file="$this_script_path/docker_exec_script_pid.txt"
    local retry_count=0
    local max_retries=5
    while [ "$retry_count" -lt "$max_retries" ]; do
        docker exec "$FLEXIV_NEBULA_CONTAINER_NAME" pgrep -f "$script_name" >> "$pid_file"
        if [ $? -eq 0 ]; then
            break
        fi
            echo "Script '$script_name' not running in container '$FLEXIV_NEBULA_CONTAINER_NAME' after $retry_count seconds"
        sleep 1
        retry_count=$((retry_count + 1))
    done

    if [ "$retry_count" -ge "$max_retries" ]; then
        echo "Warning: Script '$script_name' not running in container '$FLEXIV_NEBULA_CONTAINER_NAME' after $max_retries seconds" >&2
    fi
}

# Kill
kill_docker_exec_scripts() {
    local this_script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
    local pid_file="$this_script_path/docker_exec_script_pid.txt"
    if [ -f "$pid_file" ]; then
        while read -r pid; do
            if [[ -z "$pid" ]]; then
                echo "Ignoring empty PID"
            elif docker exec "$FLEXIV_NEBULA_CONTAINER_NAME" kill -0 "$pid" 2>/dev/null; then
                echo "Killing docker exec script PID $pid"
                docker exec "$FLEXIV_NEBULA_CONTAINER_NAME" kill "$pid"
            else
                echo "Cannot kill docker exec script PID $pid, as not running"
            fi
        done < "$pid_file"
        rm -f "$pid_file"
    fi
}
