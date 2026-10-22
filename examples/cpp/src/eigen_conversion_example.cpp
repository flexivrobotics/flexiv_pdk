/**
 * @file eigen_conversion_example.cpp
 * @brief Example: Convert between Eigen types and Flexiv PDK protobuf messages.
 *
 * Every conversion is an overload of ToEigen() or ToProto(), so the argument type picks it.
 * Each one is round-tripped here. No server is needed.
 */

#include <flexiv/pdk/physics/eigen_conversion.hpp>
#include <flexiv/pdk/spatial/eigen_conversion.hpp>

#include <cstdlib>
#include <iostream>
#include <string>

namespace physics = flexiv::pdk::physics;
namespace spatial = flexiv::pdk::spatial;

namespace {

int failures = 0;

void Check(bool ok, const std::string& what)
{
  std::cout << (ok ? "ok      " : "FAILED  ") << what << std::endl;
  failures += ok ? 0 : 1;
}

} // namespace

int main()
{
  const Eigen::Vector3d position(0.5, -0.1, 0.2);
  const Eigen::Quaterniond rotation(Eigen::AngleAxisd(0.3, Eigen::Vector3d::UnitZ()));
  Eigen::Isometry3d pose = Eigen::Isometry3d::Identity();
  pose.translation() = position;
  pose.linear() = rotation.toRotationMatrix();
  Eigen::VectorXd joints(7);
  joints << 0.0, -0.7, 0.0, 1.57, 0.0, 0.7, 0.0;
  Eigen::Matrix3d inertia;
  inertia << 0.1, 0.0, 0.0, 0.0, 0.2, 0.0, 0.0, 0.0, 0.3;

  // Vector3, Quaternion and SE3Pose
  const spatial::Vector3 position_proto = spatial::ToProto(position);
  Check(spatial::ToEigen(position_proto).isApprox(position), "Vector3d <-> Vector3");
  Check(spatial::ToEigen(spatial::ToProto(rotation)).isApprox(rotation),
      "Quaterniond <-> Quaternion");
  Check(spatial::ToEigen(spatial::Quaternion()).isApprox(Eigen::Quaterniond::Identity()),
      "an unset Quaternion is the identity");
  const spatial::SE3Pose pose_proto = spatial::ToProto(pose);
  Check(spatial::ToEigen(pose_proto).isApprox(pose), "Isometry3d <-> SE3Pose");

  // Eigen expressions pick the overload by their size
  Check(spatial::ToEigen(spatial::ToProto(pose.translation())).isApprox(position),
      "Isometry3d::translation() -> Vector3");
  Check(spatial::ToProto(joints.head(3)).size() == 3, "VectorXd::head() -> repeated double");

  // repeated double and JointWaypoint
  Check(
      spatial::ToEigen(spatial::ToProto(joints)).isApprox(joints), "VectorXd <-> repeated double");
  const spatial::JointWaypoint waypoint = spatial::ToProto(joints, Eigen::VectorXd::Zero(7));
  const auto [waypoint_position, waypoint_velocity] = spatial::ToEigen(waypoint);
  Check(waypoint_position.isApprox(joints) && waypoint_velocity.isZero(),
      "(position, velocity) <-> JointWaypoint");

  // Inertia
  Check(physics::ToEigen(physics::ToProto(inertia)).isApprox(inertia), "Matrix3d <-> Inertia");

  return failures == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
