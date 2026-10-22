# Flexiv PDK (Python)

Python package for creating robotic applications using the Flexiv PDK.
It provides the `flexiv.pdk` client and the generated gRPC message types for
talking to a Flexiv PDK server.

The [Flexiv PDK Manual](https://flexivrobotics.github.io/flexiv_pdk/) is the main reference, with tutorials, every
service, and the Python API. The source and examples are in
[flexiv_pdk](https://github.com/flexivrobotics/flexiv_pdk/tree/v1.0.0).

## Requirements

- Python 3.10+
- A running Flexiv PDK server to connect to: see
  [Install the Server](https://flexivrobotics.github.io/flexiv_pdk/install_server.html).

## Install

Pick the option that matches what you have. Both leave you with an activated
virtual environment that can `import flexiv.pdk`; afterwards continue to
[Verify your installation](#verify-your-installation).

### Option 1 — pre-built wheel (recommended for most users)

Install `flexivpdk` and its dependencies from PyPI:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "flexivpdk==<version>"
```

Use the `<version>` of the flexiv_pdk release you are using, such as `1.0.0`; it
must match the server's.

### Option 2 — from a source checkout

The SDK's gRPC stubs are generated from its `.proto` files and are not part of a
bare checkout, so a helper script does the whole setup in one step — it creates
a virtual environment, generates the stubs, and installs the SDK. From the root
of a clone of [flexiv_pdk](https://github.com/flexivrobotics/flexiv_pdk/tree/v1.0.0):

```bash
cd python
source setup_venv.sh          # source, not bash — it activates the venv for you
```

## Verify your installation

1. Confirm the package imports:

   ```bash
   python -c "from flexiv.pdk import Client; import flexiv.pdk.workcell.workcell_service_pb2; print('flexiv.pdk OK')"
   ```

2. Run a real example against a running PDK server (see
   [examples/python](https://github.com/flexivrobotics/flexiv_pdk/blob/v1.0.0/examples/python/README.md) for the full list and
   prerequisites):

   ```bash
   python examples/python/scene_example.py
   ```

## Quick usage

The `Client` class creates and manages the gRPC service client stubs.

```python
import grpc
from flexiv.pdk import Client
from flexiv.pdk.workcell.workcell_service_pb2 import NameRequest

def run_sample():
    with Client("localhost:50052") as client:
        try:
            res = client.workcell.stub.Exists(NameRequest(name="example_workcell"))
            print(f"Workcell exists: {res.exists}")
        except grpc.RpcError as e:
            print(f"Connection failed: {e}")

if __name__ == "__main__":
    run_sample()
```

A client works with a server of the same major and minor version. To check
before doing anything else:

```python
compatible, message = client.check_version()
if not compatible:
    raise SystemExit(message)
```

## Command-line interface

Installing this package also provides `pdk-scene`, a terminal tool for
inspecting and modifying a scene on a running server without writing any code:

```bash
pdk-scene --help          # list commands
pdk-scene object list     # e.g. list scene objects on the active workcell
```

Full guide: [README_CLI.md](https://github.com/flexivrobotics/flexiv_pdk/blob/v1.0.0/README_CLI.md).

## Licensed services

Most services are free. Three require a license, one each:

| Service | License code |
|---|---|
| `client.point_to_point_path` | `point_to_point_path` |
| `client.surface_finish` | `surface_finish` |
| `client.mesh_operation` | `mesh_operation` |

A license is tied to the security chip in the computer running the server, so it
needs no network at run time.

Calling one of those without a license returns `PERMISSION_DENIED` (code 5) in
the response's `status` field, and `status.message` names the service and says
what to do about it - the same check you already use for every other call. To
find out before calling, or to install a license:

```python
from flexiv.pdk.license.license_service_pb2 import ListRequest

response = client.license.stub.List(ListRequest())
for service in response.services:
    print(service.display_name, service.state, service.detail)
```

Buying a license moves two files: `pdk-scene license identifier` writes the
one you email to Flexiv, and `pdk-scene license install -f <file.lic>`
installs the one Flexiv sends back. From code, install it with the path Flexiv's
file was saved at:

```python
response = client.license.install_file("NEB-2026-0042.lic")
if response.status.code != 0:
    print(response.status.message)
```

The file is read on this machine and its contents sent over gRPC, so the server
may be another host or a container. It takes effect without a restart. The
`pdk-scene license` commands wrap the same service - see
[README_CLI.md](https://github.com/flexivrobotics/flexiv_pdk/blob/v1.0.0/README_CLI.md).

## Related docs

- The [Flexiv PDK Manual](https://flexivrobotics.github.io/flexiv_pdk/): tutorials, every service, and the Python API
- Runnable example scripts and their prerequisites: [examples/python](https://github.com/flexivrobotics/flexiv_pdk/blob/v1.0.0/examples/python/README.md)
- Repository overview: [README.md](https://github.com/flexivrobotics/flexiv_pdk/blob/v1.0.0/README.md)
