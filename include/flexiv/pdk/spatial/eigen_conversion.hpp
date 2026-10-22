#ifndef FLEXIV_PDK_SPATIAL_EIGEN_CONVERSION_HPP_
#define FLEXIV_PDK_SPATIAL_EIGEN_CONVERSION_HPP_

#include <flexiv/pdk/spatial/geometry.pb.h>
#include <flexiv/pdk/spatial/waypoint.pb.h>
#include <google/protobuf/repeated_field.h>

#include <Eigen/Dense>
#include <type_traits>
#include <utility>

namespace flexiv {
namespace pdk {
namespace spatial {

// clang-format off

Eigen::Vector3d                             ToEigen(const Vector3& v);
Eigen::Quaterniond                          ToEigen(const Quaternion& q);  // all-zero (unset) is identity
Eigen::Isometry3d                           ToEigen(const SE3Pose& p);
Eigen::VectorXd                             ToEigen(const google::protobuf::RepeatedField<double>& v);
std::pair<Eigen::VectorXd, Eigen::VectorXd> ToEigen(const JointWaypoint& waypoint);  // (position, velocity)

Vector3                                     ToProto(const Eigen::Vector3d& v);
Quaternion                                  ToProto(const Eigen::Quaterniond& q);
SE3Pose                                     ToProto(const Eigen::Isometry3d& p);
google::protobuf::RepeatedField<double>     ToProto(const Eigen::VectorXd& v);
JointWaypoint                               ToProto(const Eigen::VectorXd& joint_position,
                                                    const Eigen::VectorXd& joint_velocity);

// clang-format on

/** A 3-vector expression, such as Isometry3d::translation(), to Vector3. */
template <typename Derived, typename = std::enable_if_t<Derived::SizeAtCompileTime == 3>>
Vector3 ToProto(const Eigen::MatrixBase<Derived>& v)
{
  return ToProto(Eigen::Vector3d(v));
}

/** A dynamic-size vector expression, such as VectorXd::head(), to a repeated double field. */
template <typename Derived,
    typename = std::enable_if_t<Derived::SizeAtCompileTime == Eigen::Dynamic
                                && Derived::ColsAtCompileTime == 1>,
    typename = void>
google::protobuf::RepeatedField<double> ToProto(const Eigen::MatrixBase<Derived>& v)
{
  return ToProto(Eigen::VectorXd(v));
}

} // namespace spatial
} // namespace pdk
} // namespace flexiv

#endif
