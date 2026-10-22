cmake_minimum_required(VERSION 3.18.6)

# ===================================================================
#      PROJECT SETUP
# ===================================================================
project(pdk_cpp_examples VERSION 1.0.0)

# ===================================================================
#      APP DEPENDENCIES
# ===================================================================
# Dependencies installed by colcon
find_package(ament_cmake REQUIRED)
find_package(flexiv_pdk REQUIRED)

# ===================================================================
#      CREATE EXECUTABLE
# ===================================================================
# Create executable for scene example
add_executable(scene_example
  ../cpp/src/scene_example.cpp
)

# Set include directory
target_include_directories(scene_example PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link to dependencies
ament_target_dependencies(scene_example PUBLIC
  flexiv_pdk
)

# Create executable for point_to_point_path example
add_executable(point_to_point_path_example
  ../cpp/src/point_to_point_path_example.cpp
)

# Set include directory for point_to_point_path example
target_include_directories(point_to_point_path_example PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link to dependencies
ament_target_dependencies(point_to_point_path_example PUBLIC
  flexiv_pdk
)

# ===================================================================
#      TARGET OPTIONS
# ===================================================================
# C++17 required
set_target_properties(scene_example PROPERTIES
  CXX_STANDARD 17
  CXX_STANDARD_REQUIRED ON)
set_target_properties(point_to_point_path_example PROPERTIES
  CXX_STANDARD 17
  CXX_STANDARD_REQUIRED ON)

# Set the compilation flags
# Use moderate compiler warning setting and position-independent code
target_compile_options(scene_example PRIVATE -Wall -Wextra -fPIC)
target_compile_options(point_to_point_path_example PRIVATE -Wall -Wextra -fPIC)

install(TARGETS scene_example point_to_point_path_example
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

# ===================================================================
#      AMENT PACKAGE
# ===================================================================
ament_package()
