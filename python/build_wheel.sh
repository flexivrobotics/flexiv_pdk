#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Move to SDK root to access the 'proto' folder alongside 'python'
SDK_ROOT="${SCRIPT_DIR}/.."
cd "${SDK_ROOT}"

echo "1. Creating temporary build environment..."
python3 -m venv .build_venv
source .build_venv/bin/activate
pip install --upgrade pip build

echo "2. Generating Python Protobuf/gRPC stubs..."
# Reuse the single source of truth for stub generation. It installs
# grpcio-tools into the active environment, which here is .build_venv.
bash "${SCRIPT_DIR}/generate_protos.sh"

# The stubs refuse older grpcio/protobuf, so pyproject.toml must declare at least those
python3 "${SCRIPT_DIR}/check_stub_versions.py"

echo "3. Building the Python Wheel..."
cd "${SCRIPT_DIR}"
# Stale build output would otherwise end up in the wheel, or beside it in dist/
rm -rf build dist ./*.egg-info
# setuptools packs a LICENSE beside pyproject.toml into the wheel
cp "${SDK_ROOT}/LICENSE" LICENSE
python3 -m build --wheel
rm -f LICENSE

echo "4. Build complete!"
echo "Wheel located at: ${SCRIPT_DIR}/dist/"
deactivate
cd "${SDK_ROOT}"
rm -rf .build_venv
