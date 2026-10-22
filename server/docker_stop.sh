#!/bin/bash
FLEXIV_NEBULA_CONTAINER_NAME="${FLEXIV_NEBULA_CONTAINER_NAME:-flexiv_nebula}"
echo "Stopping Docker container $FLEXIV_NEBULA_CONTAINER_NAME. This may take a minute."
docker stop $FLEXIV_NEBULA_CONTAINER_NAME
