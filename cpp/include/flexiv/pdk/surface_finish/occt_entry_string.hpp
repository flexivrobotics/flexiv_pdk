#ifndef FLEXIV_PDK_SURFACE_FINISH_OCCT_ENTRY_STRING_HPP_
#define FLEXIV_PDK_SURFACE_FINISH_OCCT_ENTRY_STRING_HPP_

#include <string>

namespace flexiv {
namespace pdk {
namespace surface_finish {

/**
 * @brief Convert a TopoDS_Shape to an OCCT entry string
 *
 * @param shape TopoDS_Shape to convert
 * @param shapeTool XCAFDoc_ShapeTool that was used to create the shape
 * @return The OCCT entry string, or empty string if failed
 */
std::string ToOcctEntryString(
    const TopoDS_Shape& shape, const Handle(XCAFDoc_ShapeTool) & shapeTool);

} // namespace surface_finish
} // namespace pdk
} // namespace flexiv

#endif // FLEXIV_PDK_SURFACE_FINISH_OCCT_ENTRY_STRING_HPP_
