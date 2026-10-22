Install for Python
==================

Install the ``flexivpdk`` Python package. You need a running **PDK server** to
connect to; see :doc:`/install_server`.

.. note::

   The client must have the same major and minor version as the server.
   Replace ``<version>`` below with the version of the PDK release you are
   running, such as ``1.0.0``.

Requirements
------------

Python 3.10 or newer.

The Python package is called ``flexivpdk`` and is imported as ``flexiv.pdk``.
Its runtime dependencies are ``grpcio``, ``protobuf``, ``numpy``, ``scipy`` and
``click``. Both install methods below fetch them.

Install PDK package from a wheel (recommended)
----------------------------------------------

Install ``flexivpdk`` and its dependencies from PyPI:

.. code-block:: bash

   python3 -m venv .venv
   source .venv/bin/activate
   pip install "flexivpdk==<version>"

Use the version of the PDK release you are using, such as ``1.0.0``; it must
match the server's.

Install PDK package from a source checkout
------------------------------------------

A source checkout does not contain the generated gRPC stubs (``*_pb2.py``).
A helper script creates a virtual environment (``.venv`` in the repository
root), generates the stubs and installs the SDK in one step. Run it from the
repository root with ``source`` so the environment stays active:

.. code-block:: bash

   git clone https://github.com/flexivrobotics/flexiv_pdk.git
   cd flexiv_pdk
   source python/setup_venv.sh

.. important::

   If you install from source, regenerate the stubs every time you pull new
   changes (``bash python/generate_protos.sh``). Stubs older than the server's
   ``.proto`` files make the server return a bare gRPC ``INTERNAL`` error. See
   :doc:`/troubleshooting`.

Use the installed package
-------------------------

.. code-block:: bash

   python -c "from flexiv.pdk import Client; import flexiv.pdk.workcell.workcell_service_pb2; print('flexiv.pdk OK')"
   pdk-scene --help
   pdk-scene version

The examples are in the PDK repository, not in the wheel. With a wheel install,
clone the repository first. Then, from the repository root, run an example
against a server:

.. code-block:: bash

   python examples/python/scene_example.py

See :doc:`/verify_with_example_programs` for the other examples.
