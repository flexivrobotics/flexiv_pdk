#!/usr/bin/env bash
# Creates a Python virtual environment and installs flexiv_pdk from this repo.
# The default virtual environment path is <repo_root>/.venv
# The SDK is installed in editable mode so local repo changes are immediately visible
# when running Python scripts from the virtual environment.
# Usage:
#   source setup_venv.sh [VENV_PATH]
# Examples:
#   source setup_venv.sh                  # creates <repo>/.venv, configures, and activates it
#   source setup_venv.sh ~/my-application # creates custom venv path, configures, and activates it

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "Error: This script must be sourced to automatically activate the environment." >&2
  echo "Usage: source ${0} [VENV_PATH]" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ $# -ge 1 ]]; then
  VENV_PATH="$1"
else
  VENV_PATH="${REPO_ROOT}/.venv"
fi

echo "Creating virtual environment: ${VENV_PATH}"
python3 -m venv "${VENV_PATH}" || { echo "Failed to create venv." >&2; return 1; }

# shellcheck disable=SC1090
source "${VENV_PATH}/bin/activate" || { echo "Failed to activate venv." >&2; return 1; }

echo "Installing SDK from ${REPO_ROOT}/python in editable mode"
pip install --upgrade pip || { echo "Failed to upgrade pip." >&2; return 1; }

echo "Generating Python protobuf/gRPC stubs from ${REPO_ROOT}/proto"
bash "${SCRIPT_DIR}/generate_protos.sh" || {
  echo "Failed to generate protobuf/gRPC Python stubs." >&2
  return 1
}

pip install -e "${REPO_ROOT}/python" || { echo "Failed to install flexiv_pdk." >&2; return 1; }

cat <<EOF
Done. The virtual environment is now activated in your current shell.

To activate later in a new terminal:
  source "${VENV_PATH}/bin/activate"

To deactivate now or later:
  deactivate
EOF
