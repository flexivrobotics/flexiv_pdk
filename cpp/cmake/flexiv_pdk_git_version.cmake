# This macro will execute a series of git commands to define the following variables
#    - ${PROJECT_NAME}_GIT_TAG  
#    - ${PROJECT_NAME}_GIT_BRANCH
#    - ${PROJECT_NAME}_GIT_COMMIT_HASH
#    - ${PROJECT_NAME}_GIT_COMMIT_TIMESTAMP
#    - ${PROJECT_NAME}_GIT_BUILD_TIMESTAMP
# The same values are also set without the project name prefix, so that templates
# configured by this macro do not have to spell the project name out:
#    - PROJECT_GIT_TAG
#    - PROJECT_GIT_BRANCH
#    - PROJECT_GIT_COMMIT_HASH
#    - PROJECT_GIT_COMMIT_TIMESTAMP
#    - PROJECT_GIT_BUILD_TIMESTAMP
macro(flexiv_pdk_git_version)

    # get tags information
    execute_process(
      COMMAND git describe --tags
      WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
      OUTPUT_VARIABLE "${PROJECT_NAME}_GIT_TAG"
      OUTPUT_STRIP_TRAILING_WHITESPACE
      ERROR_QUIET # Hide the "No names found" error
    )

    # Get the current working branch
    execute_process(
      COMMAND git rev-parse --abbrev-ref HEAD
      WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
      OUTPUT_VARIABLE "${PROJECT_NAME}_GIT_BRANCH"
      OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    # Get the latest abbreviated commit hash of the working branch
    execute_process(
      COMMAND git rev-parse HEAD
      WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
      OUTPUT_VARIABLE "${PROJECT_NAME}_GIT_COMMIT_HASH"
      OUTPUT_STRIP_TRAILING_WHITESPACE
    )

    # get commit timestamp
    execute_process(
      COMMAND git log -1 --pretty=format:%cI
      WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
      OUTPUT_VARIABLE "${PROJECT_NAME}_GIT_COMMIT_TIMESTAMP"
      OUTPUT_STRIP_TRAILING_WHITESPACE
    )
  
    # get build timestamp
    string(TIMESTAMP "${PROJECT_NAME}_GIT_BUILD_TIMESTAMP")

    # Project-name independent aliases
    set(PROJECT_GIT_TAG "${${PROJECT_NAME}_GIT_TAG}")
    set(PROJECT_GIT_BRANCH "${${PROJECT_NAME}_GIT_BRANCH}")
    set(PROJECT_GIT_COMMIT_HASH "${${PROJECT_NAME}_GIT_COMMIT_HASH}")
    set(PROJECT_GIT_COMMIT_TIMESTAMP "${${PROJECT_NAME}_GIT_COMMIT_TIMESTAMP}")
    set(PROJECT_GIT_BUILD_TIMESTAMP "${${PROJECT_NAME}_GIT_BUILD_TIMESTAMP}")

endmacro()