cmake_minimum_required(VERSION 3.18.6)

# flexiv_pdk must be installed first (configure the repo root, then cmake --install with
# -DCMAKE_INSTALL_PREFIX=...). Configure this project with:
#   cmake -S . -B build -DCMAKE_PREFIX_PATH=<same install prefix>
# CMAKE_INSTALL_PREFIX on *this* project only controls where the examples install; it does not
# help CMake locate flexiv_pdk — use CMAKE_PREFIX_PATH (or flexiv_pdk_DIR) for that.

project(flexiv_pdk_cpp_examples VERSION 1.0.0)

find_package(flexiv_pdk REQUIRED)

set(EXAMPLES
  scene_example
  eigen_conversion_example
  components_service_example
  system_kinematics_example
  watch_scene_events_example
  point_to_point_path_example
  system_pose_example
  mesh_toolpath_raster_example
  mesh_toolpath_sketch_example
  linear_path_trajectory_generation_example
  mesh_filter_example
  mesh_area_extraction_example
  system_setup_from_rdk_example
  camera_example
  reconstruction_example
)

foreach(example ${EXAMPLES})
  add_executable(${example} src/${example}.cpp)
  target_link_libraries(${example} PRIVATE flexiv::flexiv_pdk)
  set_target_properties(${example} PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
  )
  if(CMAKE_HOST_UNIX)
    target_compile_options(${example} PRIVATE -Wall -Wextra -fPIC)
  endif()
endforeach()

include(GNUInstallDirs)
install(TARGETS ${EXAMPLES} RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
