cmake_minimum_required(VERSION 3.16.3)

# ===================================================================
#      PROJECT OPTIONS
# ===================================================================
# Prebuilt binary distribution of the flexiv_pdk_client source package: nothing is compiled here.
project(flexiv_pdk VERSION 1.0.0 LANGUAGES CXX)

# Option to manually disable ROS integration even if ROS is sourced
option(FLEXIV_PDK_ENABLE_ROS_INTEGRATION "Enable ROS 2 colcon/ament integration" ON)

# Folder under platforms/ to use. Empty means <ID>-<VERSION_ID>-<arch> of this machine.
set(FLEXIV_PDK_PLATFORM "" CACHE STRING "Prebuilt platform under platforms/, e.g. ubuntu-22.04-x86_64")

# Folder holding libflexiv_pdk.<platform>.so. Empty downloads it from the GitHub release.
set(FLEXIV_PDK_LIBRARY_DIR "" CACHE PATH "Folder holding libflexiv_pdk.<platform>.so, instead of downloading it")

# Standard CMake installation paths (bin, lib, include)
include(GNUInstallDirs)

# ===================================================================
#      SELECT PREBUILT PLATFORM
# ===================================================================
if(NOT FLEXIV_PDK_PLATFORM)
    if(NOT EXISTS "/etc/os-release")
        message(FATAL_ERROR "Cannot detect the platform: /etc/os-release not found. "
                            "Set -DFLEXIV_PDK_PLATFORM to one of the folders under platforms/.")
    endif()
    file(STRINGS "/etc/os-release" os_id REGEX "^ID=")
    file(STRINGS "/etc/os-release" os_version_id REGEX "^VERSION_ID=")
    string(REGEX REPLACE "^ID=\"?([^\"]*)\"?$" "\\1" os_id "${os_id}")
    string(REGEX REPLACE "^VERSION_ID=\"?([^\"]*)\"?$" "\\1" os_version_id "${os_version_id}")
    set(FLEXIV_PDK_PLATFORM "${os_id}-${os_version_id}-${CMAKE_SYSTEM_PROCESSOR}")
endif()

set(platform_dir "${CMAKE_CURRENT_SOURCE_DIR}/platforms/${FLEXIV_PDK_PLATFORM}")
if(NOT EXISTS "${platform_dir}/platform_info.cmake")
    file(GLOB available_platforms RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}/platforms"
         "${CMAKE_CURRENT_SOURCE_DIR}/platforms/*")
    message(FATAL_ERROR "No prebuilt flexiv_pdk for platform '${FLEXIV_PDK_PLATFORM}'. "
                        "Available: ${available_platforms}. "
                        "Set -DFLEXIV_PDK_PLATFORM to one of them if this machine is compatible.")
endif()

# Defines FLEXIV_PDK_PLATFORM_LIBRARY_VERSION, FLEXIV_PDK_PLATFORM_LIBRARY_SONAME,
# FLEXIV_PDK_PROTOBUF_VERSION and FLEXIV_PDK_CLIENT_GIT_HASH
include("${platform_dir}/platform_info.cmake")
message(STATUS "flexiv_pdk: using prebuilt platform ${FLEXIV_PDK_PLATFORM} "
               "(library ${FLEXIV_PDK_PLATFORM_LIBRARY_VERSION}, protobuf ${FLEXIV_PDK_PROTOBUF_VERSION}, "
               "commit ${FLEXIV_PDK_CLIENT_GIT_HASH})")

# ===================================================================
#      FETCH AND VERIFY THE PREBUILT LIBRARY
# ===================================================================
set(asset_name "libflexiv_pdk.${FLEXIV_PDK_PLATFORM}.so")
set(asset_url "https://github.com/flexivrobotics/flexiv_pdk/releases/download/v${PROJECT_VERSION}/${asset_name}")

file(READ "${platform_dir}/libflexiv_pdk.so.sha256" expected_hash)
string(STRIP "${expected_hash}" expected_hash)
string(TOLOWER "${expected_hash}" expected_hash)
if(NOT expected_hash MATCHES "^[0-9a-f]+$")
    message(FATAL_ERROR "${platform_dir}/libflexiv_pdk.so.sha256 does not hold a SHA-256.")
endif()
string(LENGTH "${expected_hash}" expected_hash_length)
if(NOT expected_hash_length EQUAL 64)
    message(FATAL_ERROR "${platform_dir}/libflexiv_pdk.so.sha256 does not hold a SHA-256.")
endif()

set(library_dir "${CMAKE_CURRENT_BINARY_DIR}/flexiv_pdk_lib")
set(library_file "${library_dir}/libflexiv_pdk.so.${FLEXIV_PDK_PLATFORM_LIBRARY_VERSION}")
file(MAKE_DIRECTORY "${library_dir}")

set(actual_hash "")
if(EXISTS "${library_file}")
    file(SHA256 "${library_file}" actual_hash)
endif()

if(NOT actual_hash STREQUAL expected_hash)
    if(FLEXIV_PDK_LIBRARY_DIR)
        set(local_asset "${FLEXIV_PDK_LIBRARY_DIR}/${asset_name}")
        if(NOT EXISTS "${local_asset}")
            message(FATAL_ERROR "${local_asset} not found. Put ${asset_name} from the "
                                "v${PROJECT_VERSION} release there, or unset FLEXIV_PDK_LIBRARY_DIR to download it.")
        endif()
        file(SHA256 "${local_asset}" actual_hash)
        if(NOT actual_hash STREQUAL expected_hash)
            message(FATAL_ERROR "${local_asset} does not match platforms/${FLEXIV_PDK_PLATFORM}/libflexiv_pdk.so.sha256. "
                                "Use ${asset_name} from the v${PROJECT_VERSION} release.")
        endif()
        configure_file("${local_asset}" "${library_file}" COPYONLY)
    else()
        message(STATUS "flexiv_pdk: downloading ${asset_url}")
        file(DOWNLOAD "${asset_url}" "${library_file}"
             EXPECTED_HASH SHA256=${expected_hash}
             TLS_VERIFY ON
             STATUS download_status)
        list(GET download_status 0 download_code)
        if(NOT download_code EQUAL 0)
            file(REMOVE "${library_file}")
            message(FATAL_ERROR "Downloading ${asset_url} failed: ${download_status}. "
                                "Without network access, download it elsewhere and pass "
                                "-DFLEXIV_PDK_LIBRARY_DIR=<folder holding it>.")
        endif()
    endif()
endif()

# The SONAME link is what programs load; the unversioned one is what they link
file(CREATE_LINK "libflexiv_pdk.so.${FLEXIV_PDK_PLATFORM_LIBRARY_VERSION}"
     "${library_dir}/${FLEXIV_PDK_PLATFORM_LIBRARY_SONAME}" SYMBOLIC)
file(CREATE_LINK "${FLEXIV_PDK_PLATFORM_LIBRARY_SONAME}" "${library_dir}/libflexiv_pdk.so" SYMBOLIC)

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

# The shipped *.pb.h headers only compile against the protobuf they were generated with
string(REGEX MATCH "^[0-9]+\\.[0-9]+" found_protobuf_minor "${Protobuf_VERSION}")
string(REGEX MATCH "^[0-9]+\\.[0-9]+" required_protobuf_minor "${FLEXIV_PDK_PROTOBUF_VERSION}")
if(NOT found_protobuf_minor VERSION_EQUAL required_protobuf_minor)
    message(FATAL_ERROR "flexiv_pdk for ${FLEXIV_PDK_PLATFORM} needs protobuf "
                        "${required_protobuf_minor}.x, but found protobuf ${Protobuf_VERSION}. "
                        "Install the protobuf and gRPC packages of ${FLEXIV_PDK_PLATFORM} "
                        "(see install_dependencies.sh), or use the platform that matches this machine.")
endif()

# ===================================================================
#      CREATE LIBRARY
# ===================================================================
add_library(${PROJECT_NAME} INTERFACE)

# Create an alias of the target with flexiv namespace
add_library(flexiv::${PROJECT_NAME} ALIAS ${PROJECT_NAME})

# Set include directories
target_include_directories(${PROJECT_NAME} INTERFACE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<BUILD_INTERFACE:${platform_dir}/include>
  $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)

# Link to the prebuilt library and its dependencies
target_link_libraries(${PROJECT_NAME} INTERFACE
    $<BUILD_INTERFACE:${library_dir}/libflexiv_pdk.so>
    $<INSTALL_INTERFACE:$<INSTALL_PREFIX>/${CMAKE_INSTALL_LIBDIR}/libflexiv_pdk.so>
    Eigen3::Eigen
    ${grpc_target}
    protobuf::libprotobuf
)

target_compile_features(${PROJECT_NAME} INTERFACE cxx_std_17)

# Re-check the library at install time: the build tree may have been touched since configure
install(CODE "
    file(SHA256 \"${library_file}\" installed_hash)
    if(NOT installed_hash STREQUAL \"${expected_hash}\")
        message(FATAL_ERROR \"${library_file} has changed since it was verified. Re-run CMake configure.\")
    endif()")

# Copies the .so and its symlinks
install(FILES
    "${library_file}"
    "${library_dir}/${FLEXIV_PDK_PLATFORM_LIBRARY_SONAME}"
    "${library_dir}/libflexiv_pdk.so"
    DESTINATION ${CMAKE_INSTALL_LIBDIR})

# ===================================================================
#      INSTALLATION & EXPORTS
# ===================================================================
set(use_ament FALSE)
if(FLEXIV_PDK_ENABLE_ROS_INTEGRATION)
    find_package(ament_cmake QUIET)
    if(ament_cmake_FOUND)
        set(use_ament TRUE)
    endif()
endif()

if(use_ament)
    # Standard ament installation, see
    # https://docs.ros.org/en/humble/How-To-Guides/Ament-CMake-Documentation.html#installing
    install(DIRECTORY include/ ${platform_dir}/include/
            DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
            FILES_MATCHING
            PATTERN "*.h"
            PATTERN "*.hpp"
    )
    install(TARGETS ${PROJECT_NAME}
        EXPORT "${PROJECT_NAME}-targets"
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    )
else()
    include("${CMAKE_CURRENT_SOURCE_DIR}/cmake/flexiv_pdk_install_library.cmake")
    flexiv_pdk_install_library("${CMAKE_CURRENT_SOURCE_DIR}/include;${platform_dir}/include")
endif()

# ===================================================================
#      ROS 2 / COLCON HYBRID SUPPORT
# ===================================================================
if(use_ament)
    message(STATUS "ament_cmake found. Bulding ament_package")

    ament_export_include_directories(include)
    # HAS_LIBRARY_TARGET adds lib/ to LD_LIBRARY_PATH, so the .so is found at runtime
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

    ament_package(CONFIG_EXTRAS "cmake/${PROJECT_NAME}-extras.cmake")
endif()
