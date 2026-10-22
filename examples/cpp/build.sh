#!/usr/bin/env bash
# Builds the examples into examples/cpp/build/ (Ninja/Make single-config layout).
# Requires flexiv_pdk installed (CMake config under PREFIX/lib/cmake/flexiv_pdk/).
# Override: FLEXIV_PDK_PREFIX, or set CMAKE_PREFIX_PATH (colon-separated on Unix).
# If invoking cmake yourself, use -DCMAKE_PREFIX_PATH=<sdk install>, NOT -DCMAKE_INSTALL_PREFIX
# (the latter does not tell CMake where to find flexiv_pdk).
# Parallel jobs: -j N or JOBS env (default: nproc).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
JOBS="${JOBS:-$(nproc)}"

sdk_config_file() {
  local p="$1"
  echo "${p}/lib/cmake/flexiv_pdk/flexiv_pdk-config.cmake"
}

sdk_ament_config_file() {
  local p="$1"
  echo "${p}/share/flexiv_pdk/cmake/flexiv_pdkConfig.cmake"
}

has_sdk_at() {
  [[ -f "$(sdk_config_file "$1")" || -f "$(sdk_ament_config_file "$1")" ]]
}

resolve_sdk_prefix() {
  if [[ -n "${CMAKE_PREFIX_PATH:-}" ]]; then
    local _p
    IFS=':' read -ra _paths <<< "${CMAKE_PREFIX_PATH}"
    for _p in "${_paths[@]}"; do
      [[ -z "${_p}" ]] && continue
      if has_sdk_at "${_p}"; then
        echo "${_p}"
        return 0
      fi
    done
  fi

  local candidates=(
    "${SCRIPT_DIR}/../../install"
    "${SCRIPT_DIR}/../../../../../../install"
  )
  local c
  for c in "${candidates[@]}"; do
    if has_sdk_at "${c}"; then
      echo "${c}"
      return 0
    fi
  done

  return 1
}

die_no_sdk() {
  cat >&2 <<'EOF'
error: flexiv_pdk is not installed or CMAKE cannot see it.

Install the SDK into this repo, then re-run this script:
  cd ../.. && mkdir -p build && cd build
  cmake .. -DCMAKE_INSTALL_PREFIX="$(pwd)/../install"
  cmake --install .

To configure the examples manually from examples/cpp/build (use CMAKE_PREFIX_PATH):
  cmake -S .. -B . -DCMAKE_PREFIX_PATH="$(cd ../../.. && pwd)/install"

ROS/colcon installs are also supported when the SDK package config lives under:
  <prefix>/share/flexiv_pdk/cmake/flexiv_pdkConfig.cmake

Or set FLEXIV_PDK_PREFIX to your install tree (e.g. ROS workspace install/ after colcon):
  FLEXIV_PDK_PREFIX=/path/to/install bash build.sh
EOF
  exit 1
}

extra_cmake=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -j)
      JOBS="${2:?}"
      shift 2
      ;;
    -j*)
      JOBS="${1#-j}"
      shift
      ;;
    *)
      extra_cmake+=("$1")
      shift
      ;;
  esac
done

if [[ -n "${FLEXIV_PDK_PREFIX:-}" ]]; then
  if ! has_sdk_at "${FLEXIV_PDK_PREFIX}"; then
    echo "error: FLEXIV_PDK_PREFIX=${FLEXIV_PDK_PREFIX} does not contain an installed flexiv_pdk (missing either $(sdk_config_file "${FLEXIV_PDK_PREFIX}") or $(sdk_ament_config_file "${FLEXIV_PDK_PREFIX}"))" >&2
    exit 1
  fi
  SDK_PREFIX="${FLEXIV_PDK_PREFIX}"
else
  SDK_PREFIX="$(resolve_sdk_prefix)" || die_no_sdk
fi

mkdir -p "${BUILD_DIR}"
cmake -S "${SCRIPT_DIR}" -B "${BUILD_DIR}" \
  -DCMAKE_PREFIX_PATH="${SDK_PREFIX}" \
  "${extra_cmake[@]}"
cmake --build "${BUILD_DIR}" --parallel "${JOBS}"
