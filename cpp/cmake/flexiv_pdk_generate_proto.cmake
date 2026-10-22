cmake_minimum_required(VERSION 3.16.3)

# ===================================================================
# flexiv_pdk_generate_proto
# ===================================================================
# This function creates build-time rules to generate c++ and gRPC code
# while preserving the folder structure of the source protos.
#
# Example Usage inside your main CMakeLists.txt:
#
# flexiv_pdk_generate_proto(
#     "${CMAKE_CURRENT_SOURCE_DIR}/proto"
#     "subfolder1/subfolder2" 
#     "${CMAKE_CURRENT_BINARY_DIR}/generated"
#     PROTO_HEADERS
#     PROTO_SOURCES
#     PROTO_INCLUDE_DIRECTORIES
# )
#
# add_library(${PROJECT_NAME} ${PROTO_SOURCES})
#
# target_include_directories(${PROJECT_NAME} PUBLIC 
#     $<BUILD_INTERFACE:${PROTO_INCLUDE_DIRECTORIES}>
# )
function(flexiv_pdk_generate_proto
          proto_root_path
          proto_relative_path
          output_path
          generated_header
          generated_source
          generated_include_directories
          )

    # Normalize paths
    get_filename_component(proto_root_path "${proto_root_path}" ABSOLUTE)
    get_filename_component(output_path "${output_path}" ABSOLUTE)
    file(MAKE_DIRECTORY "${output_path}")

    # Find the protoc and grpc_cpp_plugin executables
    find_program(PROTOBUF_PROTOC_EXECUTABLE NAMES protoc REQUIRED)
    find_program(GRPC_CPP_PLUGIN_EXECUTABLE NAMES grpc_cpp_plugin REQUIRED)

    # Collect absolute paths to all proto files
    if("${proto_relative_path}" STREQUAL "")
        set(proto_relative_path ".")
    endif()

    set(proto_files_abs "")
    foreach(item ${proto_relative_path})
        get_filename_component(item_abs_path "${proto_root_path}/${item}" ABSOLUTE)
        if(IS_DIRECTORY "${item_abs_path}")
            file(GLOB_RECURSE found_protos CONFIGURE_DEPENDS "${item_abs_path}/*.proto")
            list(APPEND proto_files_abs ${found_protos})
        elseif(EXISTS "${item_abs_path}")
            list(APPEND proto_files_abs "${item_abs_path}")
        endif()
    endforeach()
    list(REMOVE_DUPLICATES proto_files_abs)

    # Create build-time rules to generate C++ and gRPC code
    set(gen_headers_temp "")
    set(gen_sources_temp "")
    foreach(proto_file ${proto_files_abs})
        # Determine relative folder structure
        file(RELATIVE_PATH rel_to_root "${proto_root_path}" "${proto_file}")
        get_filename_component(rel_dir "${rel_to_root}" DIRECTORY)
        get_filename_component(filename_we "${proto_file}" NAME_WE)

        set(current_out_dir "${output_path}/${rel_dir}")
        file(MAKE_DIRECTORY "${current_out_dir}")

        # Standard Protobuf outputs (Always generated)
        set(msg_h   "${current_out_dir}/${filename_we}.pb.h")
        set(msg_cc  "${current_out_dir}/${filename_we}.pb.cc")

        # Check if the file contains a gRPC service
        file(READ "${proto_file}" PROTO_CONTENT)
        if(PROTO_CONTENT MATCHES "service[ \t]+[A-Za-z0-9_]+")
            
            set(grpc_h  "${current_out_dir}/${filename_we}.grpc.pb.h")
            set(grpc_cc "${current_out_dir}/${filename_we}.grpc.pb.cc")

            add_custom_command(
                OUTPUT "${msg_h}" "${msg_cc}" "${grpc_h}" "${grpc_cc}"
                COMMAND ${PROTOBUF_PROTOC_EXECUTABLE}
                        --proto_path=${proto_root_path}
                        --cpp_out=${output_path}
                        --grpc_out=${output_path}
                        --plugin=protoc-gen-grpc=${GRPC_CPP_PLUGIN_EXECUTABLE}
                        ${proto_file}
                DEPENDS "${proto_file}"
                COMMENT "Generating C++/gRPC for ${rel_to_root}"
                VERBATIM
            )

            list(APPEND gen_headers_temp "${msg_h}" "${grpc_h}")
            list(APPEND gen_sources_temp "${msg_cc}" "${grpc_cc}")

        else()
            
            add_custom_command(
                OUTPUT "${msg_h}" "${msg_cc}"
                COMMAND ${PROTOBUF_PROTOC_EXECUTABLE}
                        --proto_path=${proto_root_path}
                        --cpp_out=${output_path}
                        ${proto_file}
                DEPENDS "${proto_file}"
                COMMENT "Generating C++ for ${rel_to_root}"
                VERBATIM
            )

            list(APPEND gen_headers_temp "${msg_h}")
            list(APPEND gen_sources_temp "${msg_cc}")

        endif()
    endforeach()

    # Finalize and export the generated files
    set_source_files_properties(${gen_headers_temp} ${gen_sources_temp} PROPERTIES GENERATED TRUE)

    set(${generated_header} ${gen_headers_temp} PARENT_SCOPE)
    set(${generated_source} ${gen_sources_temp} PARENT_SCOPE)
    set(${generated_include_directories} "${output_path}" PARENT_SCOPE)

    message(STATUS "flexiv_pdk_generate_proto: Configured ${output_path}")
endfunction()