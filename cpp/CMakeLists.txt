cmake_minimum_required(VERSION 3.16.3)

# ===================================================================
#      PROJECT OPTIONS
# ===================================================================
project(flexiv_pdk_client VERSION 1.0.0)

# Option to manually disable ROS integration even if ROS is sourced
option(FLEXIV_PDK_ENABLE_ROS_INTEGRATION "Enable ROS 2 colcon/ament integration" ON)
option(FLEXIV_PDK_ENABLE_OCCT_INTEGRATION "Enable Open Cascade (OCCT) integration" OFF)
# The binary flexiv_pdk distribution ships the shared library; the source build stays static
option(FLEXIV_PDK_BUILD_SHARED "Build the shared libflexiv_pdk.so for the flexiv_pdk binary distribution" OFF)

# Configure build type
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "CMake build type" FORCE)
endif()

# ===================================================================
#      SETUP LIBRARY
# ===================================================================
# create a header file that defines the library version and git version
include(${CMAKE_CURRENT_SOURCE_DIR}/cmake/flexiv_pdk_git_version.cmake)
flexiv_pdk_git_version()

# this will replace @varable@ with the cmake value ${variable}
set(configured_include_directory "${CMAKE_CURRENT_BINARY_DIR}/include")
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake/version.h.in"
    "${configured_include_directory}/flexiv/pdk/common/version.h"
    )

# ===================================================================
#      PROJECT DEPENDENCIES
# ===================================================================
find_package(Eigen3 REQUIRED)
find_package(Protobuf REQUIRED)

# Try to find gRPC via Config, fallback to PkgConfig
find_package(gRPC CONFIG QUIET)
if(gRPC_FOUND)
    set(grpc_target gRPC::grpc++)
else()
    message(STATUS "gRPC Config not found, so using PkgConfig...")   
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(GRPC_PKG REQUIRED IMPORTED_TARGET grpc++)
    set(grpc_target PkgConfig::GRPC_PKG)
endif()

if(FLEXIV_PDK_ENABLE_OCCT_INTEGRATION)
    find_package(OpenCASCADE REQUIRED)
endif()

# ===================================================================
#      PROTOBUF CODE GENERATION
# ===================================================================
# List of proto sub-folders to process
set(proto_subfolders
    "."
    flexiv/pdk/camera
    flexiv/pdk/common
    flexiv/pdk/model
    flexiv/pdk/physics
    flexiv/pdk/point_to_point_path
    flexiv/pdk/scene
    flexiv/pdk/spatial
    flexiv/pdk/surface_finish
    flexiv/pdk/workcell
)

# Generate proto cpp and grpc
include("${CMAKE_CURRENT_SOURCE_DIR}/cmake/flexiv_pdk_generate_proto.cmake")
flexiv_pdk_generate_proto(
    "${CMAKE_CURRENT_SOURCE_DIR}/../proto"
    "${proto_subfolders}"
    "${CMAKE_CURRENT_BINARY_DIR}/generated"
    generated_proto_headers
    generated_proto_sources
    generated_proto_include_directories
)

# ===================================================================
#      CREATE LIBRARY
# ===================================================================
# List of cpp source files
set(cpp_source_files
    ${CMAKE_CURRENT_SOURCE_DIR}/src/client.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/session.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/watch/stream.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/watch/subscriber.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/spatial/eigen_conversion.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/physics/eigen_conversion.cpp
)

if(FLEXIV_PDK_ENABLE_OCCT_INTEGRATION)
    list(APPEND cpp_source_files
        ${CMAKE_CURRENT_SOURCE_DIR}/src/surface_finish/occt_entry_string.cpp
    )
endif()

if(FLEXIV_PDK_BUILD_SHARED)
    set(library_type SHARED)
else()
    set(library_type STATIC)
endif()

add_library(${PROJECT_NAME} ${library_type}
   ${cpp_source_files}
   ${generated_proto_sources}
)

# PIC so the static library can also be linked into shared libraries
set_target_properties(${PROJECT_NAME} PROPERTIES POSITION_INDEPENDENT_CODE ON)

if(FLEXIV_PDK_BUILD_SHARED)
    # libflexiv_pdk.so.X.Y.Z, with SONAME libflexiv_pdk.so.X, as shipped by flexiv_pdk
    set_target_properties(${PROJECT_NAME} PROPERTIES
        OUTPUT_NAME flexiv_pdk
        VERSION ${PROJECT_VERSION}
        SOVERSION ${PROJECT_VERSION_MAJOR}
    )
endif()

# Create an alias of the target with flexiv namespace
add_library(flexiv::${PROJECT_NAME} ALIAS ${PROJECT_NAME})

# Standard CMake installation paths (bin, lib, include)
include(GNUInstallDirs)

# Set include directories
target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<BUILD_INTERFACE:${configured_include_directory}>
  $<BUILD_INTERFACE:${generated_proto_include_directories}>
  $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)

# Link to dependencies
target_link_libraries(${PROJECT_NAME} PUBLIC
    Eigen3::Eigen
    ${grpc_target}
    protobuf::libprotobuf
)

if(FLEXIV_PDK_ENABLE_OCCT_INTEGRATION)
  target_include_directories(${PROJECT_NAME} PUBLIC
    $<BUILD_INTERFACE:${OpenCASCADE_INCLUDE_DIR}>
  )
  target_link_libraries(${PROJECT_NAME}  PUBLIC
    ${OpenCASCADE_LIBRARIES}
  )
endif()

# Compiler options
if(CMAKE_HOST_UNIX)
  target_compile_options(${PROJECT_NAME} PRIVATE -Wall -Wextra)
else()
  target_compile_options(${PROJECT_NAME} PRIVATE /W1)
endif()

# ===================================================================
#      SHARED LIBRARY: EXPORT ONLY THE FLEXIV API
# ===================================================================
# Same link policy as the released flexiv_rdk shared library. The version script
# exports flexiv::pdk and its generated protobuf/gRPC code, and hides the
# gRPC, protobuf and std template instantiations the library emits, so they
# cannot interpose a consumer's own. --gc-sections then drops the sections no
# export reaches, which -ffunction-sections/-fdata-sections make possible, and
# --as-needed keeps DT_NEEDED to the libraries actually used, which
# scripts/check_artifacts.sh verifies.
if(FLEXIV_PDK_BUILD_SHARED AND CMAKE_HOST_UNIX AND NOT APPLE)
  set(export_symbols_map ${CMAKE_CURRENT_SOURCE_DIR}/cmake/export_symbols.map)
  target_compile_options(${PROJECT_NAME} PRIVATE -ffunction-sections -fdata-sections)
  target_link_options(${PROJECT_NAME} PRIVATE
    "LINKER:--version-script,${export_symbols_map}"
    "LINKER:--gc-sections"
    "LINKER:--as-needed")
  set_target_properties(${PROJECT_NAME} PROPERTIES LINK_DEPENDS ${export_symbols_map})
endif()

# ===================================================================
#      INSTALLATION & EXPORTS
# ===================================================================
if(FLEXIV_PDK_ENABLE_ROS_INTEGRATION)
    find_package(ament_cmake QUIET)
    if(ament_cmake_FOUND)
        # Standard ament installation, see
        # https://docs.ros.org/en/humble/How-To-Guides/Ament-CMake-Documentation.html#installing
        install(DIRECTORY include/ ${configured_include_directory}/ ${CMAKE_CURRENT_BINARY_DIR}/generated/
                DESTINATION include
                FILES_MATCHING
                PATTERN "*.h"
                PATTERN "*.hpp"
        )
        install(TARGETS ${PROJECT_NAME} 
            EXPORT "${PROJECT_NAME}-targets"
            LIBRARY DESTINATION lib
            ARCHIVE DESTINATION lib
            RUNTIME DESTINATION bin
        )
    else()
        include("${CMAKE_CURRENT_SOURCE_DIR}/cmake/flexiv_pdk_install_library.cmake")
        flexiv_pdk_install_library("${CMAKE_CURRENT_SOURCE_DIR}/include;${configured_include_directory};${generated_proto_include_directories}")
    endif()
else() 
    include("${CMAKE_CURRENT_SOURCE_DIR}/cmake/flexiv_pdk_install_library.cmake")
    flexiv_pdk_install_library("${CMAKE_CURRENT_SOURCE_DIR}/include;${configured_include_directory};${generated_proto_include_directories}")
endif()

# ===================================================================
#      ROS 2 / COLCON HYBRID SUPPORT
# ===================================================================
if(FLEXIV_PDK_ENABLE_ROS_INTEGRATION)
    find_package(ament_cmake QUIET)
    if(ament_cmake_FOUND)
        message(STATUS "ament_cmake found. Bulding ament_package")

        ament_export_include_directories(include)
        ament_export_targets(${PROJECT_NAME}-targets HAS_LIBRARY_TARGET)

        # Exports dependencies to downstream packages so they don't need to call 
        # find_package() for those dependencies
        ament_export_dependencies(
            Eigen3
            Protobuf
        )

        # Export gRPC if it's not a standard CMake package
        if(gRPC_FOUND)
            ament_export_dependencies(gRPC)
        else()
            ament_export_dependencies(PkgConfig)
            ament_export_libraries(${GRPC_PKG_LIBRARIES})
            ament_export_include_directories(${GRPC_PKG_INCLUDE_DIRS})
        endif()

        if(FLEXIV_PDK_ENABLE_OCCT_INTEGRATION)
            ament_export_dependencies(OpenCASCADE)
        endif()

        ament_package(CONFIG_EXTRAS "cmake/${PROJECT_NAME}-extras.cmake")
    endif()
endif()
