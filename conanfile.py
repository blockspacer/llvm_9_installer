import os, shutil, glob
from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
from conans.tools import Version

# see https://github.com/conan-io/conan-center-index/blob/master/recipes/protobuf/3.9.x/conanfile.py
class Clang9InstallerConan(ConanFile):
    name = "llvm_9_installer"
    version = "master"
    description = "Conan installer for clang 9, llvm 9, iwyu, sanitizers, etc."
    topics = ("conan", "clang", "llvm", "iwyu", "include-what-you-use", "libc++", "libcpp")
    url = "https://github.com/blockspacer/llvm_9_installer"
    homepage = "https://github.com/blockspacer/llvm_9_installer"
    repo_url = 'https://github.com/blockspacer/llvm_9_installer.git'
    license = "MIT"
    exports_sources = ["LICENSE.md"]
    generators = "cmake"
    short_paths = True
    settings = "os_build", "build_type", "arch_build", "compiler", "arch"

    llvm_9_options = {
        "force_x86_64": True,
        "link_ltinfo": False,
        "include_what_you_use": False,
        "enable_msan": False,
        "enable_tsan": False,
        "enable_ubsan": False,
        "enable_asan": False
    }

    options = dict([(key, [True, False]) for key in llvm_9_options.keys()])

    default_options = llvm_9_options

    # Same as
    # self.options["llvm_9"].force_x86_64 = self.options.force_x86_64
    # self.options["llvm_9"].link_ltinfo = self.options.link_ltinfo
    # self.options["llvm_9"].include_what_you_use = self.options.include_what_you_use
    # self.options["llvm_9"].enable_msan = self.options.enable_msan
    # self.options["llvm_9"].enable_tsan = self.options.enable_tsan
    # self.options["llvm_9"].enable_ubsan = self.options.enable_ubsan
    # self.options["llvm_9"].enable_asan = self.options.enable_asan
    # etc.
    def set_dependency_options(self, dependency_name, dependency_options_dict):
        options_dict = dict([(key, value) for key, value in self.options.items()])
        for key in dependency_options_dict.keys():
          if (not key in options_dict.keys()):
            raise ConanInvalidConfiguration(str(key) + " must be in options")
          setattr(self.options[dependency_name], key, getattr(self.options, key))

    # during package step we can check populated dependency options
    # and validate that we did not forget about some dependency option
    def check_options_same(self, dependency_name, dependency_options_dict):
        for key in self.options[dependency_name].keys():
          if (not key in dependency_options_dict.keys()):
            raise ConanInvalidConfiguration(str(key) + " must be in llvm_9_options")

    # config_options() is used to configure or constraint the available options
    # in a package, before they are given a value
    def config_options(self):
        self.set_dependency_options("llvm_9", self.llvm_9_options)

    # NOTE: do not use self.settings.compiler.sanitizer
    # because it may throw ConanException if 'settings.compiler.sanitizer'
    # doesn't exist in ~/.conan/settings.yml file.
    @property
    def _sanitizer(self):
        # will return None if that setting or subsetting doesn’t exist
        # and there is no default value assigned.
        return str(self.settings.get_safe("compiler.sanitizer"))

    def configure(self):
        self.set_dependency_options("llvm_9", self.llvm_9_options)

        if self._sanitizer != 'None' \
           and not "clang" in str(self.settings.compiler):
          raise ConanInvalidConfiguration(self._sanitizer + " requires clang")

        if self._sanitizer != 'None' \
           and self.settings.compiler.libcxx != 'libc++':
          raise ConanInvalidConfiguration("sanitizers require compiler.libcxx=libc++")

    def requirements(self):
        self.requires("llvm_9/master@conan/stable")

    def package(self):
        self.check_options_same("llvm_9", self.llvm_9_options)

        self.copy(pattern="LICENSE", dst="licenses", src=self.build_folder)

    def package_id(self):
        self.info.include_build_settings()
        if self.settings.os_build == "Windows":
            del self.info.settings.arch_build # same build is used for x86 and x86_64
        del self.info.settings.arch
        del self.info.settings.compiler

    def package_info(self):
        llvm_root = self.deps_cpp_info["llvm_9"].rootpath
        self.env_info.LLVM_NORMPATH = os.path.normpath(llvm_root)
        self.output.info("llvm_9 rootpath: {}".format(llvm_root))

        self.env_info.IWYU_PATH = os.path.join(llvm_root, "bin", "include-what-you-use")
        self.env_info.CLANG_FORMAT_PATH = os.path.join(llvm_root, "bin", "clang-format")
        self.env_info.SCAN_BUILD_PATH = os.path.join(llvm_root, "bin", "scan-build")
        self.env_info.CLANG_TIDY_PATH = os.path.join(llvm_root, "bin", "clang-tidy")

        self.env_info.CPP_ANALYZER_PATH = os.path.join(llvm_root, "libexec", "c++-analyzer")
        self.env_info.CCC_ANALYZER_PATH = os.path.join(llvm_root, "libexec", "ccc-analyzer")

        for path in self.deps_cpp_info.res_paths:
            self.cpp_info.resdirs.append(path)

        self.cpp_info.includedirs.append(llvm_root)
        self.cpp_info.includedirs.append(os.path.join(llvm_root, "include"))
        for path in self.deps_cpp_info.include_paths:
            self.cpp_info.includedirs.append(path)

        self.env_info.LD_LIBRARY_PATH.append(os.path.join(llvm_root, "lib"))
        for path in self.deps_cpp_info.lib_paths:
            self.env_info.LD_LIBRARY_PATH.append(path)

        self.env_info.PATH.append(os.path.join(llvm_root, "bin"))
        self.env_info.PATH.append(os.path.join(llvm_root, "libexec"))
        for path in self.deps_cpp_info.bin_paths:
            self.env_info.PATH.append(path)

        # see https://docs.conan.io/en/latest/systems_cross_building/cross_building.html
        # and https://www.gnu.org/software/make/manual/html_node/Implicit-Variables.html
        self.env_info.CXX = os.path.join(llvm_root, "bin", "clang++")
        self.env_info.CC = os.path.join(llvm_root, "bin", "clang")
        self.env_info.AR = os.path.join(llvm_root, "bin", "llvm-ar")
        self.env_info.STRIP = os.path.join(llvm_root, "bin", "llvm-strip")
        self.env_info.LD = os.path.join(llvm_root, "bin", "ld.lld") # llvm-ld replaced by llvm-ld
        self.env_info.NM = os.path.join(llvm_root, "bin", "llvm-nm")
        # TODO: propagate to CMAKE_OBJDUMP?
        self.env_info.OBJDUMP = os.path.join(llvm_root, "bin", "llvm-objdump")
        self.env_info.SYMBOLIZER = os.path.join(llvm_root, "bin", "llvm-symbolizer")
        self.env_info.RANLIB = os.path.join(llvm_root, "bin", "llvm-ranlib")
        self.env_info.AS = os.path.join(llvm_root, "bin", "llvm-as")
        # TODO: llvm-rc-rc or llvm-rc?
        self.env_info.RC = os.path.join(llvm_root, "bin", "llvm-rc")

        common_flags = []
        if "clang" in str(self.settings.compiler) and self.settings.compiler.libcxx == 'libc++':
          common_flags.append("-lc++")
          common_flags.append("-lc++abi")
          common_flags.append("-lunwind")
          common_flags.append("-Wl,-rpath,{}/lib".format(llvm_root))
          common_flags.append("-stdlib=libc++")

        self.cpp_info.sharedlinkflags.extend(common_flags)

        self.cpp_info.exelinkflags.extend(common_flags)

        # we use libstdc++, not libstdc++
        badflag = '-stdlib=libstdc++'
        while badflag in self.env_info.LDFLAGS: self.env_info.LDFLAGS.remove(badflag)
        while badflag in self.env_info.CXXFLAGS: self.env_info.CXXFLAGS.remove(badflag)
        while badflag in self.env_info.CFLAGS: self.env_info.CFLAGS.remove(badflag)

        # we use dynamic libstdc++
        badflag = '-static-libstdc++'
        while badflag in self.env_info.LDFLAGS: self.env_info.LDFLAGS.remove(badflag)
        while badflag in self.env_info.CXXFLAGS: self.env_info.CXXFLAGS.remove(badflag)
        while badflag in self.env_info.CFLAGS: self.env_info.CFLAGS.remove(badflag)

        if "clang" in str(self.settings.compiler) and self.settings.compiler.libcxx == 'libc++':
          self.env_info.LDFLAGS.append("-stdlib=libc++")

        if "clang" in str(self.settings.compiler) and self.settings.compiler.libcxx == 'libc++':
          # https://root-forum.cern.ch/t/root-6-10-08-on-macos-high-sierra-compiling-macro-example/26651/24
          self.env_info.CXXFLAGS.append("-Wno-unused-command-line-argument")
          self.env_info.CXXFLAGS.append("-Wno-error=unused-command-line-argument")
          self.env_info.CXXFLAGS.append("-nostdinc++")
          self.env_info.CXXFLAGS.append("-nodefaultlibs")
          self.env_info.CXXFLAGS.append("-lc++abi")
          self.env_info.CXXFLAGS.append("-lc++")
          self.env_info.CXXFLAGS.append("-lm")
          self.env_info.CXXFLAGS.append("-lc")
          self.env_info.CXXFLAGS.append("-stdlib=libc++")
          self.env_info.CXXFLAGS.append("-I\"{}/include/c++/v1\"".format(llvm_root))
          self.env_info.CXXFLAGS.append("-isystem\"{}/include\"".format(llvm_root))
          self.env_info.CXXFLAGS.append("-isystem\"{}/lib/clang/9.0.1/include\"".format(llvm_root))
          self.env_info.CXXFLAGS.append("-L{}/lib".format(llvm_root))
          self.env_info.CXXFLAGS.append("-Wl,-rpath,{}/lib".format(llvm_root))
          self.env_info.CXXFLAGS.append("-resource-dir {}/lib/clang/9.0.1".format(llvm_root))

        libcxx = str(self.settings.compiler.libcxx)
        if libcxx in ["libstdc++", "libstdc++11"]:
            self.cpp_info.libs.append("stdc++")
        elif "clang" in str(self.settings.compiler) and libcxx == "libc++":
            self.cpp_info.libs.append("c++")
        elif libcxx in ["c++_static", "c++_shared"]:
            self.cpp_info.libs.extend([libcxx, "c++abi"])

        # NOTE: collects all flags, must be at the end
        self.env_info.CXXFLAGS = " ".join(self.env_info.CXXFLAGS)
        self.env_info.LDFLAGS = " ".join(self.env_info.LDFLAGS)
