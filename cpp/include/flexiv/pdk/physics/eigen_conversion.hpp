#ifndef FLEXIV_PDK_PHYSICS_EIGEN_CONVERSION_HPP_
#define FLEXIV_PDK_PHYSICS_EIGEN_CONVERSION_HPP_

#include <flexiv/pdk/physics/properties.pb.h>

#include <Eigen/Dense>

namespace flexiv {
namespace pdk {
namespace physics {

// clang-format off

Eigen::Matrix3d ToEigen(const Inertia& I);

Inertia         ToProto(const Eigen::Matrix3d& I);

// clang-format on

} // namespace physics
} // namespace pdk
} // namespace flexiv

#endif
