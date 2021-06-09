cmake_minimum_required(VERSION 3.4)

project(test_package)

# do not check compile in conanbuildinfo
# cause we will switch to other compiler after conan install
#set(CONAN_DISABLE_CHECK_COMPILER ON)
#SET(CMAKE_C_COMPILER_WORKS TRUE CACHE INTERNAL "")
#SET(CMAKE_CXX_COMPILER_WORKS TRUE CACHE INTERNAL "")
#SET(CMAKE_C_COMPILER_FORCED TRUE CACHE INTERNAL "")
#SET(CMAKE_CXX_COMPILER_FORCED TRUE CACHE INTERNAL "")
#SET(CMAKE_C_COMPILER_ID_RUN TRUE CACHE INTERNAL "")
#SET(CMAKE_CXX_COMPILER_ID_RUN TRUE CACHE INTERNAL "")

set(CMAKE_VERBOSE_MAKEFILE ON)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake/modules")
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/build/") # for conan

# do not check compile in conanbuildinfo
# cause we will switch to other compiler after conan install
# set(CONAN_DISABLE_CHECK_COMPILER ON)
# set(CMAKE_C_COMPILER_FORCED TRUE)
# set(CMAKE_CXX_COMPILER_FORCED TRUE)
# set(CMAKE_C_COMPILER_WORKS TRUE)
# set(CMAKE_CXX_COMPILER_WORKS TRUE)

option(HAS_SANITIZERS "HAS_SANITIZERS" OFF)
option(LINKS_LIBCXX "LINKS_LIBCXX" OFF)
option(LINKS_LLVM_LIBS "LINKS_LLVM_LIBS" OFF)

if(EXISTS "${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
  list(APPEND CMAKE_MODULE_PATH ${CMAKE_BINARY_DIR}/)
  include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
  include(${CMAKE_BINARY_DIR}/conan_paths.cmake OPTIONAL)
  conan_basic_setup(
    # prevent conan_basic_setup from resetting cmake variables
    TARGETS
    KEEP_RPATHS
    # see https://github.com/conan-io/conan/issues/6012
    NO_OUTPUT_DIRS
  )
else()
  message (FATAL_ERROR "must use conan")
endif()

if(NOT TARGET CONAN_PKG::llvm_9)
  message(FATAL_ERROR "Use CONAN_PKG::llvm_9 from conan")
endif()

message (STATUS "CONAN_LLVM_9_ROOT=${CONAN_LLVM_9_ROOT}")
message (STATUS "CONAN_LIB_DIRS_LLVM_9=${CONAN_LIB_DIRS_LLVM_9}")
message (STATUS "CONAN_BUILD_DIRS_LLVM_9=${CONAN_BUILD_DIRS_LLVM_9}")
message (STATUS "CONAN_INCLUDE_DIRS_LLVM_9=${CONAN_INCLUDE_DIRS_LLVM_9}")
message (STATUS "CONAN_BIN_DIRS_LLVM_9=${CONAN_BIN_DIRS_LLVM_9}")

if(NOT TARGET CONAN_PKG::llvm_9_installer)
  message(FATAL_ERROR "Use CONAN_PKG::llvm_9_installer from conan")
endif()

find_package( Threads REQUIRED )

message(STATUS "CMAKE_DL_LIBS = ${CMAKE_DL_LIBS}")

# We do not test llvm libs (libtooling, etc.) if sanitizers enabled
# or if -stdlib is libc++
if(NOT LINKS_LLVM_LIBS)
  add_executable(${PROJECT_NAME} test_package_dummy.cpp)
  target_link_libraries(${PROJECT_NAME} PUBLIC
    CONAN_PKG::llvm_9_installer
  )
else()
  add_executable(${PROJECT_NAME} test_package_libtooling.cpp)

  find_package( LLVM9 REQUIRED )

  target_include_directories(${PROJECT_NAME} PUBLIC
    ${LLVM_INCLUDE_DIRS}
    ${CLANG_INCLUDE_DIRS}
    ${CONAN_INCLUDE_DIRS_LLVM_9}
  )

  target_link_directories(${PROJECT_NAME} PUBLIC
    ${CONAN_LIB_DIRS_LLVM_9}
  )

  message(STATUS "LLVM_AVAILABLE_LIBS = ${LLVM_AVAILABLE_LIBS}")
  message(STATUS "CLANG_LIBRARIES = ${CLANG_LIBRARIES}")
  message(STATUS "LLD_LIBRARIES = ${LLD_LIBRARIES}")
  message(STATUS "LLVM_LIBRARIES = ${LLVM_LIBRARIES}")

  target_link_libraries(${PROJECT_NAME} PUBLIC
    llvm_9::llvm_9
    #llvm_9::llvm_core
    #llvm_9::clang_core
    CONAN_PKG::llvm_9_installer
  )

  find_package(llvm_9 REQUIRED)

  if(NOT TARGET CONAN_PKG::llvm_9)
    message(FATAL_ERROR "Use CONAN_PKG::llvm_9 from conan")
  endif()

  #find_library(CONAN_LIB::llvm_9_llvm_tools REQUIRED)

  if(LLVM_BINARY_DIR)
    message(STATUS "LLVM_BINARY_DIR: ${LLVM_BINARY_DIR}")
  else()
    message(FATAL_ERROR "LLVM_BINARY_DIR not found: ${LLVM_BINARY_DIR}")
  endif()

  target_compile_definitions(${PROJECT_NAME} PRIVATE
    LLVMDIR="${LLVM_BINARY_DIR}"
  )
endif()

# POSITION_INDEPENDENT_CODE for -fPIC
set_property(TARGET ${PROJECT_NAME} PROPERTY POSITION_INDEPENDENT_CODE ON)

target_link_libraries(${PROJECT_NAME} PUBLIC
  Threads::Threads
  ${CMAKE_DL_LIBS}
)

target_compile_options(${PROJECT_NAME} PRIVATE
  -fno-rtti
  -fno-exceptions)

set_target_properties( ${PROJECT_NAME} PROPERTIES
  OUTPUT_NAME ${PROJECT_NAME}
  CXX_STANDARD 17
  CXX_EXTENSIONS OFF
  CMAKE_CXX_STANDARD_REQUIRED ON
  RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
  LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib )

list(APPEND CMAKE_PROGRAM_PATH ${CONAN_BIN_DIRS})
list(APPEND CMAKE_PROGRAM_PATH ${CONAN_BIN_DIRS_LLVM_9})
list(APPEND CMAKE_PROGRAM_PATH ${CONAN_BIN_DIRS_LLVM_9_INSTALLER})

find_program(CLANG_TIDY clang-tidy
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_LLVM_9}
    ${CONAN_BIN_DIRS_LLVM_9_INSTALLER}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT CLANG_TIDY)
  message(FATAL_ERROR "CLANG_TIDY not found")
endif()

find_program(SCAN_BUILD scan-build
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_LLVM_9}
    ${CONAN_BIN_DIRS_LLVM_9_INSTALLER}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT SCAN_BUILD)
  message(FATAL_ERROR "scan-build not found")
endif()

find_program(CLANG clang
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_LLVM_9}
    ${CONAN_BIN_DIRS_LLVM_9_INSTALLER}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT CLANG)
  message(FATAL_ERROR "clang not found")
endif()

find_program(CCC_ANALYZER ccc-analyzer
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_LLVM_9}
    ${CONAN_BIN_DIRS_LLVM_9_INSTALLER}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT CCC_ANALYZER)
  message(FATAL_ERROR "ccc-analyzer not found")
endif()

find_program(CPP_ANALYZER c++-analyzer
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_LLVM_9}
    ${CONAN_BIN_DIRS_LLVM_9_INSTALLER}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT CPP_ANALYZER)
  message(FATAL_ERROR "c++-analyzer not found")
endif()

find_program(CLANG_FORMAT clang-format
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_LLVM_9}
    ${CONAN_BIN_DIRS_LLVM_9_INSTALLER}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT CLANG_FORMAT)
  message(FATAL_ERROR "clang-format not found")
endif()

find_program(IWYU include-what-you-use
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_LLVM_9}
    ${CONAN_BIN_DIRS_LLVM_9_INSTALLER}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT IWYU)
  # NOTE: not FATAL_ERROR, IWYU optional
  message(WARNING "IWYU not found")
endif()

