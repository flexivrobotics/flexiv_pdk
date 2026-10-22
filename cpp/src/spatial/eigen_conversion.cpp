#include <flexiv/pdk/spatial/eigen_conversion.hpp>

namespace flexiv {
namespace pdk {
namespace spatial {

// Vector3

Eigen::Vector3d ToEigen(const flexiv::pdk::spatial::Vector3& v)
{
  return Eigen::Vector3d(v.x(), v.y(), v.z());
}

flexiv::pdk::spatial::Vector3 ToProto(const Eigen::Vector3d& v)
{
  flexiv::pdk::spatial::Vector3 result;
  result.set_x(v.x());
  result.set_y(v.y());
  result.set_z(v.z());
  return result;
}

// Quaternion

Eigen::Quaterniond ToEigen(const flexiv::pdk::spatial::Quaternion& q)
{
  if (q.x() == 0.0 && q.y() == 0.0 && q.z() == 0.0 && q.w() == 0.0) {
    return Eigen::Quaterniond::Identity();
  }

  return Eigen::Quaterniond(q.w(), q.x(), q.y(), q.z());
}

flexiv::pdk::spatial::Quaternion ToProto(const Eigen::Quaterniond& q)
{
  flexiv::pdk::spatial::Quaternion result;
  result.set_x(q.x());
  result.set_y(q.y());
  result.set_z(q.z());
  result.set_w(q.w());
  return result;
}

// SE3Pose

Eigen::Isometry3d ToEigen(const flexiv::pdk::spatial::SE3Pose& p)
{
  Eigen::Isometry3d iso = Eigen::Isometry3d::Identity();
  iso.translation() = ToEigen(p.position());
  iso.linear() = ToEigen(p.rotation()).toRotationMatrix();
  return iso;
}

flexiv::pdk::spatial::SE3Pose ToProto(const Eigen::Isometry3d& p)
{
  flexiv::pdk::spatial::SE3Pose result;
  *result.mutable_position() = ToProto(Eigen::Vector3d(p.translation()));
  *result.mutable_rotation() = ToProto(Eigen::Quaterniond(p.linear()));
  return result;
}

// RepeatedField<double>

Eigen::VectorXd ToEigen(const google::protobuf::RepeatedField<double>& v)
{
  Eigen::VectorXd result(v.size());
  for (int i = 0; i < v.size(); ++i) {
    result(i) = static_cast<double>(v[i]);
  }
  return result;
}

google::protobuf::RepeatedField<double> ToProto(const Eigen::VectorXd& v)
{
  google::protobuf::RepeatedField<double> result;
  result.Reserve(v.size());
  for (int i = 0; i < v.size(); ++i) {
    result.Add(v(i));
  }
  return result;
}

// JointWaypoint
flexiv::pdk::spatial::JointWaypoint ToProto(
    const Eigen::VectorXd& joint_position, const Eigen::VectorXd& joint_velocity)
{
  flexiv::pdk::spatial::JointWaypoint result;
  *result.mutable_position() = ToProto(joint_position);
  *result.mutable_velocity() = ToProto(joint_velocity);
  return result;
}

std::pair<Eigen::VectorXd, Eigen::VectorXd> ToEigen(
    const flexiv::pdk::spatial::JointWaypoint& waypoint)
{
  return std::make_pair(ToEigen(waypoint.position()), ToEigen(waypoint.velocity()));
}

} // namespace spatial
} // namespace pdk
} // namespace flexiv
