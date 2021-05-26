import os, shutil, glob
from conans import ConanFile, CMake, tools, RunEnvironment
from conans.errors import ConanInvalidConfiguration
from conans.tools import Version

llvm_projects = [
  'all',
  'clang',
  'clang-tools-extra',
  'compiler-rt',
  'debuginfo-tests',
  'libc',
  'libclc',
  'libcxx',
  'libcxxabi',
  'libunwind',
  'lld',
  'lldb',
  'mlir',
  'openmp',
  'parallel-libs',
  'polly',
  'pstl'
]

default_llvm_projects = [
  'clang',
  'clang-tools-extra',
  'compiler-rt',
  'libcxx',
  'libcxxabi',
  'libunwind',
  'lld',
  'lldb'
]

llvm_targets = [
  'all',
  'AArch64',
  'AMDGPU',
  'ARM',
  'BPF',
  'Hexagon',
  'Lanai',
  'Mips',
  'MSP430',
  'NVPTX',
  'RISCV',
  'SystemZ',
  'WebAssembly',
  'X86',
  'XCore'
]

default_llvm_targets = [
  'X86'
]

llvm_libs = [
  'LLVMCore',
  'LLVMAnalysis',
  'LLVMSupport',
  'LLVMipo',
  'LLVMIRReader',
  'LLVMBinaryFormat',
  'LLVMBitReader',
  'LLVMBitWriter',
  'LLVMMC',
  'LLVMMCParser',
  'LLVMTransformUtils',
  'LLVMScalarOpts',
  'LLVMLTO',
  'LLVMCoroutines',
  'LLVMCoverage',
  'LLVMInstCombine',
  'LLVMInstrumentation',
  'LLVMLinker',
  'LLVMObjCARCOpts',
  'LLVMObject',
  'LLVMPasses',
  'LLVMProfileData',
  'LLVMTarget',
  'LLVMLibDriver',
  'LLVMLineEditor',
  'LLVMMIRParser',
  'LLVMOption',
  'LLVMRuntimeDyld',
  'LLVMSelectionDAG',
  'LLVMSymbolize',
  'LLVMTableGen',
  'LLVMVectorize',
  'clangToolingRefactoring',
  'clangStaticAnalyzerCore',
  'clangDynamicASTMatchers',
  'clangCodeGen',
  'clangFrontendTool',
  'clang',
  'clangEdit',
  'clangRewriteFrontend',
  'clangDriver',
  'clangSema',
  'clangASTMatchers',
  'clangSerialization',
  'clangBasic',
  'clangAST',
  'clangTooling',
  'clangStaticAnalyzerFrontend',
  'clangFormat',
  'clangLex',
  'clangFrontend',
  'clangRewrite',
  'clangToolingCore',
  'clangIndex',
  'clangAnalysis',
  'clangParse',
  'clangStaticAnalyzerCheckers',
  'clangARCMigrate',
]

# If your project does not depend on LLVM libs (LibTooling, etc.),
# than you can clear default_llvm_libs (just disable in options all libs)
default_llvm_libs = llvm_libs

# Sanitizer is well supported on Linux
# see https://clang.llvm.org/docs/MemorySanitizer.html#handling-external-code
llvm_sanitizers = [
  'msan',
  'tsan',
  'ubsan',
  'asan'
]

# sanitizers disabled by default
default_llvm_sanitizers = []

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
      **{
        'with_' + library : library in default_llvm_libs for library in llvm_libs },
      **{
        'with_' + project : project in default_llvm_projects for project in llvm_projects },
      **{
        'with_' + target : target in default_llvm_targets for target in llvm_targets },
      **{
        'use_sanitizer': 'None',
        'lto': 'Off',
        'exceptions': False,
        'threads': True,
        'unwind_tables': True,
        'fPIC': True,
        'shared': True,
        'rtti': False,
        'libffi': False,
        'libz': True,
        "include_what_you_use": True,
        # If `True` than will add 'LLVMCore', 'LLVMAnalysis', 'LLVMSupport',
        # 'clangAST', 'clangTooling', etc. into `self.cpp_info.libs`
        "link_with_llvm_libs": False
    }}

    options = {
      **dict([(key, 'ANY') for key in llvm_9_options.keys()]),
      **{
        # Will set `-stdlib=libc++` if `True`
        'link_libcxx': [True, False],
        # Will set `self.env_info.CXX` if `True`
        'compile_with_clang': [True, False],
    }}

    default_options = {
      **llvm_9_options,
      **{
        'link_libcxx': True,
        'compile_with_clang': True,
    }}

    # Same as
    # self.options["llvm_9"].include_what_you_use = self.options.include_what_you_use
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
        # will return None if that setting or subsetting doesn�t exist
        # and there is no default value assigned.
        return str(self.settings.get_safe("compiler.sanitizer"))

    # NOTE: we can not rely only on "compiler.sanitizer"
    # because of separate options
    @property
    def _has_sanitizer_option(self):
      return self.options.use_sanitizer != 'None'

    def configure(self):
        self.set_dependency_options("llvm_9", self.llvm_9_options)

        if self._sanitizer != 'None' \
           and not self._has_sanitizer_option:
          raise ConanInvalidConfiguration("sanitizers require options.use_sanitizer!=None")

        if self._sanitizer != 'None' \
           and not self.options.link_libcxx:
          raise ConanInvalidConfiguration("sanitizers require compiler.libcxx=libc++")

        if self._sanitizer != 'None' \
           and not self.options.compile_with_clang:
          raise ConanInvalidConfiguration("sanitizers require clang compiler")

        self.output.info("compiler is {}".format(str(self.settings.compiler)))

        if (self._sanitizer != 'None' or self._has_sanitizer_option) \
           and not "clang" in str(self.settings.compiler):
          raise ConanInvalidConfiguration("sanitizer requires clang")

    def requirements(self):
        self.output.info("requirements")

        self.requires("{}/{}@{}".format( \
          os.getenv("LLVM_9_PKG_NAME", "llvm_9"), \
          os.getenv("LLVM_9_PKG_VER", "master"), \
          os.getenv("LLVM_9_PKG_CHANNEL", "conan/stable")))

    def package(self):
        self.output.info("package")
        self.check_options_same("llvm_9", self.llvm_9_options)

        self.copy(pattern="LICENSE", dst="licenses", src=self.build_folder)

    # NOTE: It is build-time tool.
    # Any project configuration must be able to depend on it.
    def package_id(self):
        self.output.info("package_id")
        self.info.include_build_settings()
        if self.settings.os_build == "Windows":
            del self.info.settings.arch_build # same build is used for x86 and x86_64
        del self.info.settings.arch
        del self.info.settings.compiler
        del self.info.settings.build_type

    def prepend_to(self, var, value):
      return value + " " + str(var)

    def package_info(self):
        self.output.info("package_info")

        cxxflags = []
        cflags = []
        ldflags = []
        common_build_flags = []
        common_link_flags = []

        llvm_root = self.deps_cpp_info["llvm_9"].rootpath
        self.env_info.LLVM_NORMPATH = os.path.normpath(llvm_root)
        self.output.info("llvm_9 rootpath: {}".format(llvm_root))

        self.env_info.IWYU_PATH = os.path.join(llvm_root, "bin", "include-what-you-use")
        self.env_info.CLANG_FORMAT_PATH = os.path.join(llvm_root, "bin", "clang-format")
        self.env_info.SCAN_BUILD_PATH = os.path.join(llvm_root, "bin", "scan-build")
        self.env_info.CLANG_TIDY_PATH = os.path.join(llvm_root, "bin", "clang-tidy")

        self.env_info.CPP_ANALYZER_PATH = os.path.join(llvm_root, "libexec", "c++-analyzer")
        self.env_info.CCC_ANALYZER_PATH = os.path.join(llvm_root, "libexec", "ccc-analyzer")

        if self.options.link_libcxx:
          for path in self.deps_cpp_info.res_paths:
              self.cpp_info.resdirs.append(path)

        if self.options.link_libcxx:
          self.cpp_info.includedirs.append(llvm_root)
          self.cpp_info.includedirs.append(os.path.join(llvm_root, "include"))
          for path in self.deps_cpp_info.include_paths:
              self.cpp_info.includedirs.append(path)

        if self.options.link_libcxx:
          self.env_info.LD_LIBRARY_PATH.append(os.path.join(llvm_root, "lib"))
          for path in self.deps_cpp_info.lib_paths:
              self.env_info.LD_LIBRARY_PATH.append(path)

        self.env_info.PATH.append(os.path.join(llvm_root, "bin"))
        self.env_info.PATH.append(os.path.join(llvm_root, "libexec"))
        for path in self.deps_cpp_info.bin_paths:
            self.env_info.PATH.append(path)

        if self.options.compile_with_clang:
          # see https://docs.conan.io/en/latest/systems_cross_building/cross_building.html
          # and https://www.gnu.org/software/make/manual/html_node/Implicit-Variables.html
          self.env_info.CXX = os.path.join(llvm_root, "bin", "clang++")
          if not os.path.exists(self.env_info.CXX):
            raise Exception("Unable to find path: {}".format(self.env_info.CXX))

          self.env_info.CC = os.path.join(llvm_root, "bin", "clang")
          if not os.path.exists(self.env_info.CC):
            raise Exception("Unable to find path: {}".format(self.env_info.CC))

          # TODO: use llvm-ar or llvm-lib?
          self.env_info.AR = os.path.join(llvm_root, "bin", "llvm-ar")
          if not os.path.exists(self.env_info.AR):
            raise Exception("Unable to find path: {}".format(self.env_info.AR))

          self.env_info.STRIP = os.path.join(llvm_root, "bin", "llvm-strip")
          if not os.path.exists(self.env_info.STRIP):
            raise Exception("Unable to find path: {}".format(self.env_info.STRIP))

          # TODO: use lld-link or ld.lld?
          # NOTE: llvm-ld replaced by llvm-ld
          self.env_info.LD = os.path.join(llvm_root, "bin", "ld.lld")
          if not os.path.exists(self.env_info.LD):
            raise Exception("Unable to find path: {}".format(self.env_info.LD))

          self.env_info.NM = os.path.join(llvm_root, "bin", "llvm-nm")
          if not os.path.exists(self.env_info.NM):
            raise Exception("Unable to find path: {}".format(self.env_info.NM))

          self.env_info.LLVM_CONFIG_PATH = os.path.join(llvm_root, "bin", "llvm-config")
          if not os.path.exists(self.env_info.LLVM_CONFIG_PATH):
            raise Exception("Unable to find path: {}".format(self.env_info.LLVM_CONFIG_PATH))

          # TODO: propagate to CMAKE_OBJDUMP?
          self.env_info.OBJDUMP = os.path.join(llvm_root, "bin", "llvm-objdump")
          if not os.path.exists(self.env_info.OBJDUMP):
            raise Exception("Unable to find path: {}".format(self.env_info.OBJDUMP))

          self.env_info.SYMBOLIZER = os.path.join(llvm_root, "bin", "llvm-symbolizer")
          if not os.path.exists(self.env_info.SYMBOLIZER):
            raise Exception("Unable to find path: {}".format(self.env_info.SYMBOLIZER))

          self.env_info.RANLIB = os.path.join(llvm_root, "bin", "llvm-ranlib")
          if not os.path.exists(self.env_info.RANLIB):
            raise Exception("Unable to find path: {}".format(self.env_info.RANLIB))

          # TODO: use llvm-as or clang?
          self.env_info.AS = os.path.join(llvm_root, "bin", "llvm-as")
          if not os.path.exists(self.env_info.STRIP):
            raise Exception("Unable to find path: {}".format(self.env_info.AS))

          # TODO: use llvm-rc-rc or llvm-rc
          self.env_info.RC = os.path.join(llvm_root, "bin", "llvm-rc")
          if not os.path.exists(self.env_info.RC):
            raise Exception("Unable to find path: {}".format(self.env_info.RC))

        # Preaload libs or add to
        # LD_PRELOAD=.../lib/clang/9.0.0/lib/x86_64-unknown-linux-gnu/libclang_rt.asan.so
        if (self._sanitizer != 'None' or self._has_sanitizer_option):
          clang_libdir = os.path.join(llvm_root, "lib/clang/9.0.0/lib")
          clang_libpaths = [os.path.join(clang_libdir, f) for f in os.listdir(clang_libdir)]
          self.output.info("clang_libpaths = {}".format(str(clang_libpaths)))
          # loop over
          # lib/clang/9.0.0/lib/linux,
          # lib/clang/9.0.0/lib/x86_64-unknown-linux-gnu,
          # etc.
          for path in clang_libpaths:
            common_build_flags.append("-L{}".format(path))
            common_build_flags.append("-Wl,-rpath,{}".format(path))
            common_link_flags.append("-L{}".format(path))
            common_link_flags.append("-Wl,-rpath,{}".format(path))
            self.cpp_info.libdirs.extend(["{}/lib".format(path)])
            for sanlib in ['libclang_rt.lsan.so', 'libclang_rt.asan.so', \
                           'libclang_rt.tsan.so', 'libclang_rt.msan.so', \
                           'libclang_rt.ubsan.so']:
              if os.path.exists("{}/{}".format(path, sanlib)):
                self.env_info.LD_PRELOAD.append("{}/{}".format(path, sanlib))

          # if not os.path.exists(clang_libdir):
          #   raise ConanInvalidConfiguration(str(clang_libdir) + " must exist")
          # clang_libpaths = []
          # clang_libpaths.append("-lc++")
          # self.env_info.LD_LIBRARY_PATH.extend(clang_libpaths)

        #self.output.info("self.env_info.LD_PRELOAD = {}".format(self.env_info.LD_PRELOAD)))

        if self.options.link_libcxx:
          common_link_flags.append("-lc++")
          common_link_flags.append("-lc++abi")
          common_link_flags.append("-lunwind")
          common_link_flags.append("-Wl,-rpath,{}/lib".format(llvm_root))
          common_link_flags.append("-stdlib=libc++")

        if self.options.link_libcxx:
          # we use libstdc++, not libstdc++
          badflag = '-stdlib=libstdc++'
          while badflag in self.env_info.LDFLAGS:
            self.env_info.LDFLAGS.remove(badflag)
          while badflag in self.env_info.CXXFLAGS:
            self.env_info.CXXFLAGS.remove(badflag)
          while badflag in self.env_info.CFLAGS:
            self.env_info.CFLAGS.remove(badflag)

        # TODO: do we need '-static-libstdc++' support at all?
        # if self.options.link_libcxx:
        #   badflag = '-static-libstdc++'
        #   while badflag in self.env_info.LDFLAGS:
        #     self.env_info.LDFLAGS.remove(badflag)
        #   while badflag in self.env_info.CXXFLAGS:
        #     self.env_info.CXXFLAGS.remove(badflag)
        #   while badflag in self.env_info.CFLAGS:
        #     self.env_info.CFLAGS.remove(badflag)

        if (len(self._sanitizer) and self._sanitizer != 'None') \
          or (len(str(self.options.use_sanitizer)) and self.options.use_sanitizer != "None"):
          llvm_symbolizer = "{}/bin/llvm-symbolizer".format(llvm_root)
          self.env_info.UBSAN_SYMBOLIZER_PATH = llvm_symbolizer
          self.env_info.ASAN_SYMBOLIZER_PATH = llvm_symbolizer
          self.env_info.TSAN_SYMBOLIZER_PATH = llvm_symbolizer
          self.env_info.MSAN_SYMBOLIZER_PATH = llvm_symbolizer

        if self.options.link_libcxx:
          ldflags.append("-stdlib=libc++")

        if self.options.link_libcxx:
          # https://root-forum.cern.ch/t/root-6-10-08-on-macos-high-sierra-compiling-macro-example/26651/24
          common_build_flags.append("-Wno-unused-command-line-argument")
          common_build_flags.append("-Wno-error=unused-command-line-argument")
          common_build_flags.append("-nostdinc++")
          common_build_flags.append("-nodefaultlibs")
          common_build_flags.append("-lc++abi")
          common_build_flags.append("-lunwind")
          common_build_flags.append("-lc++")
          common_build_flags.append("-lm")
          common_build_flags.append("-lc")
          common_build_flags.append("-stdlib=libc++")
          common_build_flags.append("-isystem{}/include/c++/v1".format(llvm_root))
          common_build_flags.append("-isystem\"{}/include\"".format(llvm_root))
          common_build_flags.append("-isystem\"{}/lib/clang/9.0.0/include\"".format(llvm_root))
          common_build_flags.append("-L{}/lib".format(llvm_root))
          common_build_flags.append("-Wl,-rpath,{}/lib".format(llvm_root))
          #cxxflags.append("-resource-dir {}/lib/clang/9.0.0".format(llvm_root))
          self.cpp_info.libdirs.extend(["{}/lib".format(llvm_root)])

        # if self._libcxx in ["libstdc++", "libstdc++11"]:
        #     self.cpp_info.libs.append("stdc++")
        # elif "clang" in str(self.settings.compiler) and self._libcxx == "libc++":
        #     self.cpp_info.libs.append("c++")
        # elif self._libcxx in ["c++_static", "c++_shared"]:
        #     self.cpp_info.libs.extend([self._libcxx, "c++abi"])

        self.cpp_info.cxxflags.extend(common_build_flags)
        self.cpp_info.cxxflags.extend(cxxflags)
        self.cpp_info.cflags.extend(common_build_flags)
        self.cpp_info.cflags.extend(cflags)
        self.cpp_info.sharedlinkflags.extend(common_link_flags)
        self.cpp_info.exelinkflags.extend(common_link_flags)
        self.cpp_info.sharedlinkflags.extend(ldflags)
        self.cpp_info.exelinkflags.extend(ldflags)

        # NOTE: collects all flags, must be at the end
        self.env_info.CXXFLAGS = " ".join(self.cpp_info.cxxflags)
        self.env_info.LDFLAGS = " ".join(self.cpp_info.sharedlinkflags)
