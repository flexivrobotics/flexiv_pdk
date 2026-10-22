"""Conversion functions between NumPy arrays and Flexiv PDK protobuf types.

Equivalent to: cpp/include/flexiv/pdk/spatial/eigen_conversion.hpp

Quaternions are ``[w, x, y, z]``, as in Eigen. An all-zero (unset) protobuf
``Quaternion`` reads as the identity rotation. A ``JointWaypoint`` converts to and
from a ``(position, velocity)`` pair, as in C++.
"""

from typing import List, Optional, Sequence, Tuple, Type, Union, overload

import numpy as np
from numpy.typing import ArrayLike
from scipy.spatial.transform import Rotation

from flexiv.pdk.spatial.geometry_pb2 import Quaternion, SE3Pose, Vector3
from flexiv.pdk.spatial.waypoint_pb2 import JointWaypoint

_Target = Union[Type[Vector3], Type[Quaternion], Type[SE3Pose], Type[JointWaypoint], Type[list]]


def _wxyz(q: Quaternion) -> List[float]:
    if q.w == 0.0 and q.x == 0.0 and q.y == 0.0 and q.z == 0.0:
        return [1.0, 0.0, 0.0, 0.0]
    return [q.w, q.x, q.y, q.z]


@overload
def to_numpy(message: JointWaypoint) -> Tuple[np.ndarray, np.ndarray]: ...
@overload
def to_numpy(message: Union[Vector3, Quaternion, SE3Pose, Sequence[float]]) -> np.ndarray: ...


def to_numpy(message):
    """Converts a protobuf message or repeated field to a NumPy array.

    Args:
        message: ``Vector3`` -> ``[x, y, z]``; ``Quaternion`` -> ``[w, x, y, z]``;
            ``SE3Pose`` -> 4x4 homogeneous matrix; ``JointWaypoint`` ->
            ``(position, velocity)``; a ``repeated double`` field, list or
            tuple -> 1-D array.

    Returns:
        A ``float64`` array, or a pair of them for a ``JointWaypoint``.

    Raises:
        TypeError: ``message`` is none of the above.
    """
    if isinstance(message, Vector3):
        return np.array([message.x, message.y, message.z], dtype=np.float64)
    if isinstance(message, Quaternion):
        return np.array(_wxyz(message), dtype=np.float64)
    if isinstance(message, SE3Pose):
        w, x, y, z = _wxyz(message.rotation)
        transform = np.eye(4, dtype=np.float64)
        transform[:3, :3] = Rotation.from_quat([x, y, z, w]).as_matrix()
        transform[:3, 3] = to_numpy(message.position)
        return transform
    if isinstance(message, JointWaypoint):
        return to_numpy(message.position), to_numpy(message.velocity)
    if isinstance(message, (str, bytes)) or not isinstance(message, Sequence):
        raise TypeError(
            f"to_numpy() takes a Vector3, Quaternion, SE3Pose, JointWaypoint or repeated double field, "
            f"not {type(message).__name__}")
    return np.array(message, dtype=np.float64)


@overload
def to_proto(value: Rotation, target: Optional[Type[Quaternion]] = None) -> Quaternion: ...
@overload
def to_proto(value: ArrayLike, target: Type[Vector3]) -> Vector3: ...
@overload
def to_proto(value: ArrayLike, target: Type[Quaternion]) -> Quaternion: ...
@overload
def to_proto(value: ArrayLike, target: Optional[Type[SE3Pose]] = None) -> SE3Pose: ...
@overload
def to_proto(value: Tuple[ArrayLike, ArrayLike], target: Type[JointWaypoint]) -> JointWaypoint: ...
@overload
def to_proto(value: ArrayLike, target: Type[list]) -> List[float]: ...


def to_proto(value, target=None):
    """Converts a NumPy array or SciPy rotation to a protobuf message.

    A 4x4 matrix and a ``Rotation`` need no ``target``. A 1-D array does: three
    numbers can be a position or three joints.

    Args:
        value: A ``scipy.spatial.transform.Rotation``, or anything
            ``np.asarray`` accepts.
        target: ``Vector3`` for ``[x, y, z]``; ``Quaternion`` for
            ``[w, x, y, z]`` or a ``Rotation``; ``SE3Pose`` for a 4x4
            homogeneous matrix; ``JointWaypoint`` for a ``(position,
            velocity)`` pair of 1-D arrays; ``list`` for a ``repeated double``
            field.

    Returns:
        A message of type ``target``, or a list of floats for ``list``.

    Raises:
        TypeError: ``target`` is missing for a 1-D array, or is not one of the
            above.
        ValueError: ``value`` has the wrong shape for ``target``.
    """
    if isinstance(value, Rotation):
        if target not in (None, Quaternion):
            raise TypeError(f"A Rotation converts to Quaternion, not {target.__name__}")
        x, y, z, w = value.as_quat()
        return Quaternion(w=w, x=x, y=y, z=z)

    if target is JointWaypoint:
        if len(value) != 2:
            raise ValueError("to_proto(value, JointWaypoint) needs a (position, velocity) pair")
        position, velocity = value
        return JointWaypoint(position=to_proto(position, list),
                             velocity=to_proto(velocity, list))

    array = np.asarray(value, dtype=np.float64)
    if target is None:
        if array.shape == (4, 4):
            target = SE3Pose
        else:
            raise TypeError(
                f"to_proto() needs a target for an array of shape {array.shape}: "
                f"Vector3, Quaternion or list, e.g. to_proto(p, Vector3)")

    if target is SE3Pose:
        _check_shape(array, (4, 4), target)
        x, y, z, w = Rotation.from_matrix(array[:3, :3]).as_quat()
        return SE3Pose(position=Vector3(x=array[0, 3], y=array[1, 3], z=array[2, 3]),
                       rotation=Quaternion(w=w, x=x, y=y, z=z))
    if target is Vector3:
        _check_shape(array, (3,), target)
        return Vector3(x=array[0], y=array[1], z=array[2])
    if target is Quaternion:
        _check_shape(array, (4,), target)
        return Quaternion(w=array[0], x=array[1], y=array[2], z=array[3])
    if target is list:
        if array.ndim != 1:
            raise ValueError(f"to_proto(value, list) needs a 1-D array, not shape {array.shape}")
        return array.tolist()
    raise TypeError(
        f"to_proto() target must be Vector3, Quaternion, SE3Pose, JointWaypoint or list, not {target!r}")


def _check_shape(array: np.ndarray, shape: tuple, target: _Target) -> None:
    if array.shape != shape:
        raise ValueError(
            f"to_proto(value, {target.__name__}) needs shape {shape}, not {array.shape}")
