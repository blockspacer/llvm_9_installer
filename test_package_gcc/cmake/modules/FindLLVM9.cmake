if(NOT TARGET CONAN_PKG::llvm_9)
  message(FATAL_ERROR "Use CONAN_PKG::llvm_9 from conan")
endif()

message (STATUS "CONAN_LLVM_9_ROOT=${CONAN_LLVM_9_ROOT}")
message (STATUS "CONAN_LIB_DIRS_LLVM_9_CONAN=${CONAN_LIB_DIRS_LLVM_9_CONAN}")
message (STATUS "CONAN_BUILD_DIRS_LLVM_9_CONAN=${CONAN_BUILD_DIRS_LLVM_9_CONAN}")
message (STATUS "CONAN_INCLUDE_DIRS_LLVM_9_CONAN=${CONAN_INCLUDE_DIRS_LLVM_9_CONAN}")

find_path(LLVMConfig_DIR LLVMConfig.cmake
          HINTS
                ${CONAN_LLVM_9_ROOT}
                ${CONAN_LLVM_9_ROOT}/lib/cmake/llvm
                ${CONAN_LIB_DIRS_LLVM_9_CONAN}
                ${CONAN_BUILD_DIRS_LLVM_9_CONAN}
                ${CONAN_INCLUDE_DIRS_LLVM_9_CONAN}
          NO_DEFAULT_PATH)

message(STATUS "[LLVM_9] LLVMConfig_DIR: ${LLVMConfig_DIR}")

include(
  ${LLVMConfig_DIR}/LLVMConfig.cmake
)

if(LLVM_BINARY_DIR)
  message(STATUS "[LLVM_9] LLVM_BINARY_DIR: ${LLVM_BINARY_DIR}")
else()
  message(FATAL_ERROR "[LLVM_9] LLVM_BINARY_DIR not found: ${LLVM_BINARY_DIR}")
endif()

list(APPEND LLVM_9_DEFINITIONS LLVMDIR="${LLVM_BINARY_DIR}")

find_path(ClangConfig_DIR ClangConfig.cmake
          HINTS
                ${CONAN_LLVM_9_ROOT}
                ${CONAN_LLVM_9_ROOT}/lib/cmake/clang
                ${CONAN_LLVM_9_ROOT}/clang/cmake/modules
                ${CONAN_LIB_DIRS_LLVM_9_CONAN}
                ${CONAN_BUILD_DIRS_LLVM_9_CONAN}
                ${CONAN_INCLUDE_DIRS_LLVM_9_CONAN}
          NO_DEFAULT_PATH)

message(STATUS "[LLVM_9] ClangConfig_DIR: ${ClangConfig_DIR}")

include(
  ${ClangConfig_DIR}/ClangConfig.cmake
)

message(STATUS "Found Clang ${CLANG_PACKAGE_VERSION}")
message(STATUS "Using ClangConfig.cmake in: ${ClangConfig_DIR}")
if(NOT EXISTS "${CONAN_LLVM_9_ROOT}/lib/cmake/llvm")
  message(FATAL_ERROR "not found: ${CONAN_LLVM_9_ROOT}/lib/cmake/llvm")
endif()
