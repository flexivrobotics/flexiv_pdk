#include <flexiv/pdk/surface_finish/occt_entry_string.hpp>

#include <sstream>
#include <stdexcept>

namespace flexiv {
namespace pdk {
namespace surface_finish {

#include <TCollection_AsciiString.hxx>
#include <TDF_Tool.hxx>
#include <TopAbs_ShapeEnum.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Shape.hxx>
#include <XCAFDoc_ShapeTool.hxx>
#include <iostream>
#include <string>

std::string ToOcctEntryString(
    const TopoDS_Shape& shape, const Handle(XCAFDoc_ShapeTool) & shapeTool)
{
  if (shape.IsNull()) {
    return "";
  }

  TDF_Label label;
  TCollection_AsciiString entry_string;
  if (shapeTool->Search(shape, label)) {
    TDF_Tool::Entry(label, entry_string);
  }

  return entry_string.ToCString();
}

} // namespace surface_finish
} // namespace pdk
} // namespace flexiv
