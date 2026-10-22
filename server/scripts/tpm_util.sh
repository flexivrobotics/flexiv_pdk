#!/bin/bash
# Helpers for giving the Nebula container access to the host's TPM 2.0 chip,
# which is what licensed features are bound to.
#
# There is deliberately no host daemon here. /dev/tpmrm0 is the kernel's own TPM
# resource manager, so the server in the container can talk to the chip directly
# and nothing has to be installed as root at runtime.
#
# Source this file, then use:
#     get_tpm_docker_option TPM_OPTION        # docker run arguments (may be empty)
#     grant_container_tpm_access "$container" # after the container is running
#
# Both are safe on machines with no TPM: the option comes back empty and the
# server falls back to basic features only.

# Path the container uses. The kernel resource manager multiplexes access, so we
# never need the raw /dev/tpm0.
readonly TPM_RESOURCE_MANAGER_DEVICE=/dev/tpmrm0

# Build the docker run arguments needed for TPM access.
#
# $1: name of the variable to write the arguments into.
get_tpm_docker_option() {
  local -n _out="$1"
  _out=""

  if [ ! -e "$TPM_RESOURCE_MANAGER_DEVICE" ]; then
    echo "[tpm] No $TPM_RESOURCE_MANAGER_DEVICE on this host."
    echo "[tpm] Nebula will start normally, with licensed features switched off."
    return 0
  fi

  _out="--device=${TPM_RESOURCE_MANAGER_DEVICE}:${TPM_RESOURCE_MANAGER_DEVICE}"
  echo "[tpm] Passing $TPM_RESOURCE_MANAGER_DEVICE into the container."
}

# Let the container's 'flexiv' user read the TPM device.
#
# The device is owned by the host's 'tss' group, and the container needs a group
# with the same numeric id. This is done after the container starts rather than
# with `docker run --group-add`, because the image's entrypoint switches to the
# 'flexiv' user with gosu, which resolves supplementary groups from the
# container's own /etc/group and so drops anything --group-add added.
#
# Every `docker exec --user flexiv` session started afterwards - including the
# one that runs the server - picks the group up.
#
# $1: container name.
grant_container_tpm_access() {
  local container="$1"

  if [ ! -e "$TPM_RESOURCE_MANAGER_DEVICE" ]; then
    return 0
  fi

  local host_tss_gid
  host_tss_gid="$(stat -c '%g' "$TPM_RESOURCE_MANAGER_DEVICE" 2>/dev/null)"
  if [ -z "$host_tss_gid" ]; then
    echo "[tpm] Could not read the group of $TPM_RESOURCE_MANAGER_DEVICE; skipping."
    return 0
  fi

  # Create (or renumber) a 'tss_host' group inside the container to match, and
  # put 'flexiv' in it. -o allows a duplicate gid, which happens when the host's
  # tss gid collides with a group the image already has.
  if docker exec --user root "$container" bash -c "
        groupadd -o -g $host_tss_gid tss_host 2>/dev/null || \
        groupmod -o -g $host_tss_gid tss_host 2>/dev/null || true
        usermod -aG tss_host flexiv" >/dev/null 2>&1; then
    echo "[tpm] Container user 'flexiv' can now read the TPM (group id $host_tss_gid)."
  else
    echo "[tpm] WARNING: could not grant TPM access inside the container."
    echo "[tpm] Licensed features will be switched off."
  fi

  # Deliberately no check on whether the host user can read the device: the
  # container process opens it, using the group id granted above, so the person
  # who ran this script does not need to be in the host's 'tss' group.
  # setup_tpm_access.sh is only for running TPM tools on the host.
}
