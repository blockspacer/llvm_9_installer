from conans import ConanFile, CMake, tools, RunEnvironment
import os

class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake", "cmake_find_package", "cmake_paths"

    @property
    def _has_sanitizers(self):
      return self.options["llvm_9_installer"].use_sanitizer != 'None'

    # def build_requirements(self):
    #     # https://github.com/conan-io/conan/issues/8466
    #     self.build_requires("llvm_9_installer/{}@{}/{}".format(\
    #       self.requires["llvm_9_installer"].ref.version, \
    #       self.requires["llvm_9_installer"].ref.user, \
    #       self.requires["llvm_9_installer"].ref.channel))
    #
    # def requirements(self):
    #     self.output.info("requirements")
    #
    #     self.requires("{}/{}@{}".format( \
    #       os.getenv("LLVM_9_PKG_NAME", "llvm_9"), \
    #       os.getenv("LLVM_9_PKG_VER", "master"), \
    #       os.getenv("LLVM_9_PKG_CHANNEL", "conan/stable")))

    def build(self):

        #print("env ",self.env)                                 # ok
        #print("environ ",os.environ)                       # ok
        #print("deps_cpp_info ", self.deps_cpp_info["llvm_9_installer"])    # ok
        #print("deps_env_info ", self.deps_env_info["llvm_9_installer"])    # fails
        #
        #self.old_env = dict(os.environ)

        # see https://github.com/conan-io/conan/issues/1858
        # env = tools.environment_append(RunEnvironment(self).vars)
        # deps_env = self.deps_cpp_info["llvm_9_installer"].components["clang_compiler"].env_info
        # with tools.environment_append(deps_env):

        cmake = CMake(self)
        cmake.parallel = True
        cmake.verbose = True
        cmake.definitions["LINKS_LIBCXX"] = "ON" \
          if self.options["llvm_9_installer"].link_libcxx else "OFF"
        cmake.definitions["HAS_SANITIZERS"] = "ON" \
          if self._has_sanitizers else "OFF"
        cmake.definitions["LINKS_LLVM_LIBS"] = "ON" \
          if self.options["llvm_9_installer"].link_with_llvm_libs else "OFF"
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

            llvm_root = self.deps_cpp_info["llvm_9"].rootpath
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
            extra_flags.append("-isystem\"{}/lib/clang/9.0.1/include\"".format(llvm_root))
            #extra_flags.append("-L{}/lib".format(llvm_root))
            #extra_flags.append("-Wl,-rpath,{}/lib".format(llvm_root))
            extra_flags.append("-resource-dir\"={}/lib/clang/9.0.1\"".format(llvm_root))

            # test that libtooling can parse source file
            self.run(command=bin_path \
              + " " + " ".join("-extra-arg=%s" % f for f in extra_flags)
              + " " + str(os.path.join(self.source_folder, "test_package_dummy.cpp")), run_environment=True)

