get_gpu_docker_option() {
    local has_gpu=false
    local enable_gpu="$1"
    declare -n gpu_docker_option="$2"  # nameref to caller's variable

    # Check if GPU is present
    if lspci | grep -i -E "nvidia" >/dev/null 2>&1; then
        has_gpu=true
    fi

    if [[ "$enable_gpu" == true && "$has_gpu" == true ]]; then
        echo "GPU enabled."
        gpu_docker_option="--gpus all"
    elif [[ "$enable_gpu" != true && "$has_gpu" == true ]]; then
        echo "GPU detected, but not enabled."
        gpu_docker_option=""
    elif [[ "$enable_gpu" == true && "$has_gpu" != true ]]; then
        echo "WARNING: Cannot enable GPU, as none detected."
        gpu_docker_option=""
    else
        echo "GPU not detected."
        gpu_docker_option=""
    fi
}