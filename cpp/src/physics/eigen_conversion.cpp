#include <flexiv/pdk/physics/eigen_conversion.hpp>

namespace flexiv {
namespace pdk {
namespace physics {

// Inertia

Eigen::Matrix3d ToEigen(const flexiv::pdk::physics::Inertia& I)
{
  Eigen::Matrix3d matrix;
  matrix(0, 0) = I.ixx();
  matrix(1, 1) = I.iyy();
  matrix(2, 2) = I.izz();
  matrix(0, 1) = matrix(1, 0) = I.ixy();
  matrix(0, 2) = matrix(2, 0) = I.ixz();
  matrix(1, 2) = matrix(2, 1) = I.iyz();
  return matrix;
}

flexiv::pdk::physics::Inertia ToProto(const Eigen::Matrix3d& I)
{
  flexiv::pdk::physics::Inertia result;
  result.set_ixx(I(0, 0));
  result.set_iyy(I(1, 1));
  result.set_izz(I(2, 2));
  result.set_ixy(I(0, 1));
  result.set_ixz(I(0, 2));
  result.set_iyz(I(1, 2));
  return result;
}

} // namespace physics
} // namespace pdk
} // namespace flexiv
