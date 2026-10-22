"""
Example: Convert between NumPy arrays and Flexiv PDK protobuf messages.

Every conversion is to_numpy() or to_proto() from flexiv.pdk.spatial or
flexiv.pdk.physics, and the message type picks it. Each one is round-tripped
here. No server is needed.
"""
import sys

import numpy as np
from scipy.spatial.transform import Rotation

from flexiv.pdk import physics, spatial
from flexiv.pdk.spatial.geometry_pb2 import Quaternion, SE3Pose, Vector3
from flexiv.pdk.spatial.waypoint_pb2 import JointWaypoint

failures = 0


def check(ok, what):
    global failures
    print(f"{'ok      ' if ok else 'FAILED  '}{what}")
    failures += 0 if ok else 1


def main():
    position = np.array([0.5, -0.1, 0.2])
    rotation = Rotation.from_rotvec([0.0, 0.0, 0.3])
    pose = np.eye(4)
    pose[:3, :3] = rotation.as_matrix()
    pose[:3, 3] = position
    joints = np.array([0.0, -0.7, 0.0, 1.57, 0.0, 0.7, 0.0])
    inertia = np.diag([0.1, 0.2, 0.3])

    # Vector3, Quaternion and SE3Pose
    position_proto = spatial.to_proto(position, Vector3)
    check(np.allclose(spatial.to_numpy(position_proto), position), "ndarray <-> Vector3")
    wxyz = spatial.to_numpy(spatial.to_proto(rotation))
    check(np.allclose(Rotation.from_quat([*wxyz[1:], wxyz[0]]).as_matrix(), rotation.as_matrix()),
          "Rotation <-> Quaternion")
    check(np.allclose(spatial.to_numpy(Quaternion()), [1.0, 0.0, 0.0, 0.0]),
          "an unset Quaternion is the identity")
    pose_proto = spatial.to_proto(pose)
    check(isinstance(pose_proto, SE3Pose) and np.allclose(spatial.to_numpy(pose_proto), pose),
          "4x4 ndarray <-> SE3Pose")

    # Slices convert like any other array
    check(np.allclose(spatial.to_numpy(spatial.to_proto(pose[:3, 3], Vector3)), position),
          "pose[:3, 3] -> Vector3")
    check(len(spatial.to_proto(joints[:3], list)) == 3, "joints[:3] -> repeated double")

    # repeated double and JointWaypoint
    check(np.allclose(spatial.to_numpy(spatial.to_proto(joints, list)), joints),
          "ndarray <-> repeated double")
    waypoint = spatial.to_proto((joints, np.zeros(7)), JointWaypoint)
    waypoint_position, waypoint_velocity = spatial.to_numpy(waypoint)
    check(np.allclose(waypoint_position, joints) and not waypoint_velocity.any(),
          "(position, velocity) <-> JointWaypoint")

    # Inertia
    check(np.allclose(physics.to_numpy(physics.to_proto(inertia)), inertia), "3x3 ndarray <-> Inertia")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
