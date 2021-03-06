if(NOT TARGET CONAN_PKG::${LLVM_PACKAGE_NAME})
  message(FATAL_ERROR "Use CONAN_PKG::${LLVM_PACKAGE_NAME} from conan")
endif()

message (STATUS "CONAN_${LLVM_PACKAGE_NAME_UPPER}_ROOT=${CONAN_${LLVM_PACKAGE_NAME_UPPER}_ROOT}")
message (STATUS "CONAN_LIB_DIRS_${LLVM_PACKAGE_NAME_UPPER}_CONAN=${CONAN_LIB_DIRS_${LLVM_PACKAGE_NAME_UPPER}_CONAN}")
message (STATUS "CONAN_BUILD_DIRS_${LLVM_PACKAGE_NAME_UPPER}_CONAN=${CONAN_BUILD_DIRS_${LLVM_PACKAGE_NAME_UPPER}_CONAN}")
message (STATUS "CONAN_INCLUDE_DIRS_${LLVM_PACKAGE_NAME_UPPER}_CONAN=${CONAN_INCLUDE_DIRS_${LLVM_PACKAGE_NAME_UPPER}_CONAN}")

find_path(LLVMConfig_DIR LLVMConfig.cmake
          HINTS
                ${CONAN_${LLVM_PACKAGE_NAME_UPPER}_ROOT}
                ${CONAN_${LLVM_PACKAGE_NAME_UPPER}_ROOT}/lib/cmake/llvm
                ${CONAN_LIB_DIRS_${LLVM_PACKAGE_NAME_UPPER}_CONAN}
                ${CONAN_BUILD_DIRS_${LLVM_PACKAGE_NAME_UPPER}_CONAN}
                ${CONAN_INCLUDE_DIRS_${LLVM_PACKAGE_NAME_UPPER}_CONAN}
          NO_DEFAULT_PATH)

message(STATUS "[${LLVM_PACKAGE_NAME_UPPER}] LLVMConfig_DIR: ${LLVMConfig_DIR}")

include(
  ${LLVMConfig_DIR}/LLVMConfig.cmake
)

if(LLVM_BINARY_DIR)
  message(STATUS "[${LLVM_PACKAGE_NAME_UPPER}] LLVM_BINARY_DIR: ${LLVM_BINARY_DIR}")
else()
  message(FATAL_ERROR "[${LLVM_PACKAGE_NAME_UPPER}] LLVM_BINARY_DIR not found: ${LLVM_BINARY_DIR}")
endif()

list(APPEND ${LLVM_PACKAGE_NAME_UPPER}_DEFINITIONS LLVMDIR="${LLVM_BINARY_DIR}")

find_path(ClangConfig_DIR ClangConfig.cmake
          HINTS
                ${CONAN_${LLVM_PACKAGE_NAME_UPPER}_ROOT}
                ${CONAN_${LLVM_PACKAGE_NAME_UPPER}_ROOT}/lib/cmake/clang
                ${CONAN_${LLVM_PACKAGE_NAME_UPPER}_ROOT}/clang/cmake/modules
                ${CONAN_LIB_DIRS_${LLVM_PACKAGE_NAME_UPPER}_CONAN}
                ${CONAN_BUILD_DIRS_${LLVM_PACKAGE_NAME_UPPER}_CONAN}
                ${CONAN_INCLUDE_DIRS_${LLVM_PACKAGE_NAME_UPPER}_CONAN}
          NO_DEFAULT_PATH)

message(STATUS "[${LLVM_PACKAGE_NAME_UPPER}] ClangConfig_DIR: ${ClangConfig_DIR}")

include(
  ${ClangConfig_DIR}/ClangConfig.cmake
)

message(STATUS "Found Clang ${CLANG_PACKAGE_VERSION}")
message(STATUS "Using ClangConfig.cmake in: ${ClangConfig_DIR}")
if(NOT EXISTS "${CONAN_${LLVM_PACKAGE_NAME_UPPER}_ROOT}/lib/cmake/llvm")
  message(FATAL_ERROR "not found: ${CONAN_${LLVM_PACKAGE_NAME_UPPER}_ROOT}/lib/cmake/llvm")
endif()
