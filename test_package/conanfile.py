from conans import ConanFile, CMake, tools, RunEnvironment
import os

def get_name(default):
    envvar = os.getenv("LLVM_INSTALLER_PACKAGE_NAME", default)
    return envvar

class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake", "cmake_find_package", "cmake_paths"

    @property
    def _parent_options(self):
      return self.options[get_name("llvm_9_installer")]

    @property
    def _has_sanitizers(self):
      return self._parent_options.use_sanitizer != 'None'

    def build(self):

        cmake = CMake(self)
        cmake.parallel = True
        cmake.verbose = True
        cmake.definitions["LINKS_LIBCXX"] = "ON" \
          if self._parent_options.link_libcxx else "OFF"
        cmake.definitions["HAS_SANITIZERS"] = "ON" \
          if self._has_sanitizers else "OFF"
        cmake.definitions["LINKS_LLVM_LIBS"] = "ON" \
          if self._parent_options.link_with_llvm_libs else "OFF"
        cmake.definitions["LLVM_PACKAGE_NAME"] = self._parent_options.LLVM_PKG_NAME
        #cmake.definitions["CONAN_DISABLE_CHECK_COMPILER"] = "ON"
        #cmake.definitions["CMAKE_CXX_COMPILER_ID"] = ""
        #cmake.definitions["CMAKE_C_COMPILER_ID"] = ""
        #cmake.definitions["CMAKE_C_COMPILER_WORKS"] = ""
        #cmake.definitions["CMAKE_CXX_COMPILER_WORKS"] = ""
        #cmake.definitions["CMAKE_C_COMPILER_FORCED"] = ""
        #cmake.definitions["CMAKE_CXX_COMPILER_FORCED"] = ""
        #cmake.definitions["CMAKE_C_COMPILER_ID_RUN"] = ""
        #cmake.definitions["CMAKE_CXX_COMPILER_ID_RUN"] = ""
        cmake.configure()
        cmake.build()

        #os.environ.clear()
        #os.environ.update(self.old_env)

    def test(self):
        with tools.environment_append(RunEnvironment(self).vars):
          #print("environ ",os.environ)
          bin_path = os.path.join("bin", "test_package")

          if self._has_sanitizers:
            # We do not test llvm libs (libtooling, etc.) if sanitizers enabled
            self.run(command=bin_path, run_environment=True)
          else:
            # must run without error
            self.run(command=bin_path + " --version", run_environment=True)

            llvm_root = self.deps_cpp_info[str(self._parent_options.LLVM_PKG_NAME)].rootpath
            extra_flags = []
            #extra_flags.append("-nostdinc")
            extra_flags.append("-nostdinc++")
            #extra_flags.append("-stdlib=libc++")
            #extra_flags.append("-lc")
            #extra_flags.append("-lc++")
            #extra_flags.append("-lc++abi")
            #extra_flags.append("-lm")
            #extra_flags.append("-lunwind")
            extra_flags.append("-I\"{}/include/c++/v1\"".format(llvm_root))
            extra_flags.append("-isystem\"{}/include\"".format(llvm_root))
            extra_flags.append("-isystem\"{}/lib/clang/12.0.1/include\"".format(llvm_root))
            #extra_flags.append("-L{}/lib".format(llvm_root))
            #extra_flags.append("-Wl,-rpath,{}/lib".format(llvm_root))

            llvm_v = os.getenv("LLVM_CONAN_CLANG_VER", "9.0.1")
            extra_flags.append("-resource-dir\"={}/lib/clang/{}\"".format(llvm_root, llvm_v))

            # test that libtooling can parse source file
            self.run(command=bin_path \
              + " " + " ".join("-extra-arg=%s" % f for f in extra_flags)
              + " " + str(os.path.join(self.source_folder, "test_package_dummy.cpp")), run_environment=True)

