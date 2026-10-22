#!/usr/bin/env python3
"""Check that pyproject.toml declares the grpcio/protobuf the generated stubs need.

Stubs from grpcio-tools refuse to import on an older grpcio or protobuf runtime,
so the wheel's dependency floors must be at least what they were generated for.
Run after generate_protos.sh:

    python3 check_stub_versions.py [--pyproject PATH]
"""

import argparse
import pathlib
import re
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent

GRPC_GENERATED = re.compile(r"^GRPC_GENERATED_VERSION = '([\d.]+)'", re.MULTILINE)
PROTOBUF_GENERATED = re.compile(
    r"ValidateProtobufRuntimeVersion\(\s*_runtime_version\.Domain\.PUBLIC,"
    r"\s*(\d+),\s*(\d+),\s*(\d+),"
)


def parse_version(text):
    return tuple(int(part) for part in text.split("."))


def format_version(version):
    return ".".join(str(part) for part in version)


def required_versions(stub_root):
    """Returns the highest grpcio and protobuf versions any stub asks for."""
    grpc_files = list(stub_root.rglob("*_pb2_grpc.py"))
    pb2_files = list(stub_root.rglob("*_pb2.py"))
    if not pb2_files:
        sys.exit(
            f"error: no generated *_pb2.py under {stub_root}. Run generate_protos.sh first."
        )

    grpc_needed = None
    for path in grpc_files:
        match = GRPC_GENERATED.search(path.read_text())
        if match:
            version = parse_version(match.group(1))
            grpc_needed = max(grpc_needed or version, version)

    protobuf_needed = None
    for path in pb2_files:
        match = PROTOBUF_GENERATED.search(path.read_text())
        if match:
            version = tuple(int(group) for group in match.groups())
            protobuf_needed = max(protobuf_needed or version, version)

    return grpc_needed, protobuf_needed


def declared_floor(pyproject_text, package, pyproject):
    match = re.search(rf'"{package}>=([\d.]+)', pyproject_text)
    if not match:
        sys.exit(f'error: {pyproject} has no "{package}>=X" dependency. Add one.')
    return parse_version(match.group(1))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--pyproject",
        type=pathlib.Path,
        default=SCRIPT_DIR / "pyproject.toml",
        help="pyproject.toml to check (default: the one beside this script)",
    )
    args = parser.parse_args()

    grpc_needed, protobuf_needed = required_versions(SCRIPT_DIR / "flexiv")
    pyproject_text = args.pyproject.read_text()

    errors = []
    for package, needed in (("grpcio", grpc_needed), ("protobuf", protobuf_needed)):
        if needed is None:
            print(f"{package}: the stubs do not check its version")
            continue
        floor = declared_floor(pyproject_text, package, args.pyproject)
        if floor < needed:
            errors.append(
                f"stubs need {package}>={format_version(needed)} but {args.pyproject} "
                f"declares {package}>={format_version(floor)}; raise the floor"
            )
        else:
            print(
                f"{package}: stubs need >={format_version(needed)}, "
                f"pyproject declares >={format_version(floor)}"
            )

    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
