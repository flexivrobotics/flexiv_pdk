#!/bin/bash
FLEXIV_NEBULA_CONTAINER_NAME="${FLEXIV_NEBULA_CONTAINER_NAME:-flexiv_nebula}"
echo "Opening Bash shell in Docker container $FLEXIV_NEBULA_CONTAINER_NAME" 
docker exec --user flexiv -it $FLEXIV_NEBULA_CONTAINER_NAME bash
