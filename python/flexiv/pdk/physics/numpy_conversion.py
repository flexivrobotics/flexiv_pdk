"""Conversion functions between NumPy arrays and Flexiv PDK physics messages.

Equivalent to: cpp/include/flexiv/pdk/physics/eigen_conversion.hpp

An ``Inertia`` converts to and from its symmetric 3x3 inertia tensor.
"""

from typing import Optional, Type

import numpy as np
from numpy.typing import ArrayLike

from flexiv.pdk.physics.properties_pb2 import Inertia


def to_numpy(message: Inertia) -> np.ndarray:
    """Converts an ``Inertia`` to its symmetric 3x3 inertia tensor.

    Args:
        message: The ``Inertia`` to convert.

    Returns:
        A ``float64`` 3x3 array.

    Raises:
        TypeError: ``message`` is not an ``Inertia``.
    """
    if not isinstance(message, Inertia):
        raise TypeError(f"to_numpy() takes an Inertia, not {type(message).__name__}")
    return np.array([[message.ixx, message.ixy, message.ixz],
                     [message.ixy, message.iyy, message.iyz],
                     [message.ixz, message.iyz, message.izz]], dtype=np.float64)


def to_proto(value: ArrayLike, target: Optional[Type[Inertia]] = None) -> Inertia:
    """Converts a 3x3 inertia tensor to an ``Inertia``.

    Only the upper triangle is read, as in C++.

    Args:
        value: Anything ``np.asarray`` accepts, of shape ``(3, 3)``.
        target: ``Inertia``, or ``None``, which means the same.

    Returns:
        An ``Inertia``.

    Raises:
        TypeError: ``target`` is not ``Inertia``.
        ValueError: ``value`` is not 3x3.
    """
    if target not in (None, Inertia):
        raise TypeError(f"to_proto() target must be Inertia, not {target!r}")
    matrix = np.asarray(value, dtype=np.float64)
    if matrix.shape != (3, 3):
        raise ValueError(f"to_proto(value, Inertia) needs shape (3, 3), not {matrix.shape}")
    return Inertia(ixx=matrix[0, 0], iyy=matrix[1, 1], izz=matrix[2, 2],
                   ixy=matrix[0, 1], ixz=matrix[0, 2], iyz=matrix[1, 2])
