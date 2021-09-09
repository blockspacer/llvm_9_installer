from conans import ConanFile, CMake, tools, RunEnvironment
import os

def get_name(default):
    envvar = os.getenv("LLVM_INSTALLER_PACKAGE_NAME", default)
    return envvar

class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake", "cmake_find_package"

    @property
    def _parent_options(self):
      return self.options[get_name("llvm_9_installer")]

    def build(self):
        cmake = CMake(self)
        cmake.definitions["LLVM_PACKAGE_NAME"] = self._parent_options.LLVM_PKG_NAME
        cmake.configure()
        cmake.build()

    def test(self):
        with tools.environment_append(RunEnvironment(self).vars):
          #print("environ ",os.environ)
          bin_path = os.path.join("bin", "test_package")
          self.run(command=bin_path, run_environment=True)
