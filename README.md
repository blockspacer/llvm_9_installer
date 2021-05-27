# About

This package is useful as a conan `build_requires`

Features:

* allows to build code using clang 9
* bundles libc++ i.e. -stdlib=libc++ -lc++abi -lc++ -lm -lc
* bundles lld as linker i.e. -fuse-ld=lld
* bundles std header files i.e. -I.../include/c++/v1 -I.../include -nostdinc++ -nodefaultlibs
* bundles clang-tidy, scan-build, ccc-analyzer, c++-analyzer, clang-format to analyze and modify source files
* bundles LLVM libs. For example, `LibTooling` can be used to parse source code.
* (conan option) can bundle include-what-you-use to analyze #includes of source files
* (conan option) can bundle google-sanitizers: ASAN - memory error detector, MSAN - detects the use of uninitialized memory, TSAN - data race detector, etc.

## Motivation

* Make sure everyone uses same compiler, std headers, linker, libc++, etc.
* Avoid conflicts with system libs, headers, etc. when using bundled 'libc++' ("-nostdinc++", "-nodefaultlibs", etc.)
* Set env. vars automatically i.e. UBSAN_SYMBOLIZER_PATH will point to llvm-symbolizer when self.settings.get_safe("compiler.sanitizer") == 'Memory'
* Set paths in CXXFLAGS to compiler headers and libs in LDFLAGS automatically
* Set LD_PRELOAD sanitiled `clang_rt` libs automatically i.e. preloads libs in `.../lib/clang/{clang_version}/lib/{platform_name}/libclang_rt.*san-{platform_target}.so`

## How it works

`llvm_9_installer` sets CC, CXX, etc. environment variables similar to https://docs.conan.io/en/latest/systems_cross_building/cross_building.html

Note that `llvm_9_installer` creates environment variables in conanfile.py i.e. `self.env_info.RC = os.path.join(llvm_root, "bin", "llvm-rc")`, etc.

Add in conanfile.py:

```python
    def build_requirements(self):
        self.build_requires("llvm_9_installer/master@conan/stable")
```

You may need to link with `CONAN_PKG::llvm_9_installer` to propagate compiler and linker flags:

```cmake
target_link_libraries(${PROJECT_NAME} PRIVATE
  CONAN_PKG::llvm_9_installer
)
```

If you want to link with shared llvm libs i.e. LibTooling, etc., than add in conanfile.py:

```python
    def requirements(self):
      self.requires("llvm_9/master@conan/stable")
```

Usually you do not need to link with llvm libs, in that case no need to add `self.requires("llvm_9/master@conan/stable")`.

Create and use special conan profile, see `Usage` section below.

## How to link with some llvm, clang, tooling, etc. libs

CXX11_ABI is modeled by settings.compiler.libcxx

LLVM conan recipe does not have compiler setting
beacuse clang++ does not depend on arch

But tooling libs depend on arch...
You must use same CXX ABI as LLVM libs
otherwise you will get link errors!

## Before installation

Follow instructions in README to build `conan_llvm_9`:

How to build and install `conan_llvm_9`: https://github.com/blockspacer/conan_llvm_9

`llvm_9_installer` is wrapper around `conan_llvm_9`

## NOTE: `llvm_9_installer` options must match `llvm_9` options

If you build code with `llvm_9_installer:use_sanitizer=Thread`,
than you need to build LLVM with `llvm_9:use_sanitizer=Thread`

If you build code with `llvm_9_installer:link_with_llvm_libs=True`,
than you need to build LLVM with `llvm_9:link_with_llvm_libs=False`

etc.

See `llvm_9_options` in `conanfile.py` to detect options that are shared between `llvm_9` and `llvm_9_installer`

Some options unique used only by `llvm_9_installer`.
For example, if you build code with `llvm_9_installer:link_libcxx=False`,
than you do not need to re-build LLVM (`llvm_9` does not have `link_libcxx` option)

## How to avoid `llvm_9` re-builds per each change in options

Imagine that you work on multiple projects and need to store at the same time `llvm_9`
package with shared linkage, with static linkage, with sanitizers, without sanitizers, etc.

If you need to use multiple `llvm_9` versions with different options at same time,
than you can change `BUILD_NUMBER` env. var. during `llvm_9` build, example:
`BUILD_NUMBER=-static-sanitized conan export-pkg . my_channel/release`
and change env. vars during `llvm_9_installer` build:
* LLVM_9_PKG_NAME - defaults to "llvm_9"
* LLVM_9_PKG_VER - defaults to "master"
* LLVM_9_PKG_CHANNEL - defaults to "conan/stable"

## Build and install

Conan profile (in `~/.conan/profiles`) must use same CXX ABI as used LLVM libs, example profile:

Create clang9 profile:

```bash
[settings]
os_build=Linux
os=Linux
arch_build=x86_64
arch=x86_64

compiler=clang
compiler.version=9
compiler.libcxx=libc++

llvm_9:build_type=Release

[build_requires]
cmake_installer/3.15.5@conan/stable

[options]
llvm_9_installer:compile_with_clang=True
```

```bash
export VERBOSE=1
export CONAN_REVISIONS_ENABLED=1
export CONAN_VERBOSE_TRACEBACK=1
export CONAN_PRINT_RUN_COMMANDS=1
export CONAN_LOGGING_LEVEL=10
export GIT_SSL_NO_VERIFY=true

rm -rf test_package/build/
rm -rf local_build_iwyu

cmake -E time \
  conan install . \
  --install-folder local_build_iwyu \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  -o llvm_9_installer:compile_with_clang=True \
  -o llvm_9_installer:link_libcxx=False \
  --profile clang9

cmake -E time \
    conan source . \
    --source-folder local_build_iwyu \
    --install-folder local_build_iwyu

conan build . \
    --build-folder local_build_iwyu \
    --source-folder local_build_iwyu \
    --install-folder local_build_iwyu

# remove before `conan export-pkg`
(CONAN_REVISIONS_ENABLED=1 \
    conan remove --force llvm_9_installer || true)

conan package . \
    --build-folder local_build_iwyu \
    --package-folder local_build_iwyu/package_dir \
    --source-folder local_build_iwyu \
    --install-folder local_build_iwyu

conan export-pkg . \
    conan/stable \
    --package-folder local_build_iwyu/package_dir \
    --settings build_type=Release \
    --force \
    -s llvm_9:build_type=Release \
    -o llvm_9_installer:compile_with_clang=True \
    -o llvm_9_installer:link_libcxx=False \
    --profile clang9

cmake -E time \
  conan test test_package llvm_9_installer/master@conan/stable \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  -o llvm_9_installer:compile_with_clang=True \
  -o llvm_9_installer:link_libcxx=False \
  --profile clang9

rm -rf local_build_iwyu/package_dir
```

## How to build with LLVM libs support.

LLVM libs support - For example, `LibTooling` can be used to parse source code.

Create clang_9_cxx11abi_llvm_libs profile:

```bash
[settings]
os=Linux
os_build=Linux
arch=x86_64
arch_build=x86_64
compiler=clang
compiler.version=9
compiler.libcxx=libstdc++11
build_type=Release

[options]
llvm_9_installer:compile_with_clang=True
llvm_9_installer:link_libcxx=False
llvm_9_installer:link_with_llvm_libs=True
llvm_9_installer:include_what_you_use=False
```

You `--profile` below based on compiler used during LLVM compilation (clang or gcc)

```bash
cmake -E time \
  conan create . \
  conan/stable \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  -o llvm_9_installer:compile_with_clang=True \
  -o llvm_9_installer:link_libcxx=False \
  -o llvm_9_installer:link_with_llvm_libs=True \
  --profile clang_9_cxx11abi_llvm_libs
```

Conan flow:

```bash
export VERBOSE=1
export CONAN_REVISIONS_ENABLED=1
export CONAN_VERBOSE_TRACEBACK=1
export CONAN_PRINT_RUN_COMMANDS=1
export CONAN_LOGGING_LEVEL=10
export GIT_SSL_NO_VERIFY=true

rm -rf test_package/build/
rm -rf local_build_llvm_libs

cmake -E time \
  conan install . \
  --install-folder local_build_llvm_libs \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  -o llvm_9_installer:compile_with_clang=True \
  -o llvm_9_installer:link_libcxx=False \
  -o llvm_9_installer:link_with_llvm_libs=True \
  --profile clang_9_cxx11abi_llvm_libs

cmake -E time \
    conan source . \
    --source-folder local_build_llvm_libs \
    --install-folder local_build_llvm_libs

conan build . \
    --build-folder local_build_llvm_libs \
    --source-folder local_build_llvm_libs \
    --install-folder local_build_llvm_libs

# remove before `conan export-pkg`
(CONAN_REVISIONS_ENABLED=1 \
    conan remove --force llvm_9_installer || true)

conan package . \
    --build-folder local_build_llvm_libs \
    --package-folder local_build_llvm_libs/package_dir \
    --source-folder local_build_llvm_libs \
    --install-folder local_build_llvm_libs

conan export-pkg . \
    conan/stable \
    --package-folder local_build_llvm_libs/package_dir \
    --settings build_type=Release \
    --force \
    -s llvm_9:build_type=Release \
    -o llvm_9_installer:compile_with_clang=True \
    -o llvm_9_installer:link_libcxx=False \
    -o llvm_9_installer:link_with_llvm_libs=True \
    --profile clang_9_cxx11abi_llvm_libs

cmake -E time \
  conan test test_package llvm_9_installer/master@conan/stable \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  -o llvm_9_installer:compile_with_clang=True \
  -o llvm_9_installer:link_libcxx=False \
  -o llvm_9_installer:link_with_llvm_libs=True \
  --profile clang_9_cxx11abi_llvm_libs

rm -rf local_build_llvm_libs/package_dir
```

## Usage with libc++ (link_libcxx=True)

Create conan profile `~.conan/profiles/clang_libcpp`:

```bash
[settings]
os_build=Linux
os=Linux
arch_build=x86_64
arch=x86_64

compiler=clang
compiler.version=9
compiler.libcxx=libc++

build_type=Release
llvm_9:build_type=Release

[options]
llvm_9_installer:link_libcxx=True

[build_requires]
cmake_installer/3.15.5@conan/stable
llvm_9_installer/master@conan/stable
```

Note that you may need to change some `llvm_9` options, based on desired configuration.

Now you can use `conan create` command with created conan profile:

```bash
conan create . \
  conan/stable \
  -s build_type=Release \
  --profile clang_libcpp \
  --build missing
```

Note `--profile clang_libcpp` above.

If you want to create sanitized package, than use command similar to:

```bash
# Example profile `~.conan/profiles/clang_libcpp_asan` can be found below (need to scroll a bit)
conan create . \
  conan/stable \
  -s build_type=Release \
  --profile clang_libcpp_asan \
  -s llvm_9:build_type=Release \
  -o llvm_9_installer:include_what_you_use=False \
  -o llvm_9_installer:use_sanitizer="Address;Undefined"
```

## How to run llvm tools (clang-tidy, clang-format, etc.)

Use `find_program` to find required llvm tool, see README in https://github.com/blockspacer/conan_llvm_9 for details

Example code that uses clang tidy: https://github.com/blockspacer/cmake_helper_utils_conan/blob/master/cmake/Findcmake_helper_utils.cmake#L1260

## How to enable lld

Edit `~.conan/profiles/{{YOUR_PROFILE_NAME_HERE}}` and add into `[env]` section `LDFLAGS=-fuse-ld=lld`.

## How to use with clang-format

Use cmake `find_program` with `CONAN_BIN_DIRS_LLVM_9` in `PATHS`.

See `clang_format_enabler` in https://github.com/blockspacer/cmake_helper_utils_conan/blob/master/cmake/Findcmake_helper_utils.cmake

## How to use with clang-tidy

Use cmake `find_program` with `CONAN_BIN_DIRS_LLVM_9` in `PATHS`.

See `clang_tidy_enabler` in https://github.com/blockspacer/cmake_helper_utils_conan/blob/master/cmake/Findcmake_helper_utils.cmake

## How to use with include_what_you_use

Use cmake `find_program` with `CONAN_BIN_DIRS_LLVM_9` in `PATHS`.

See `iwyu_enabler` in https://github.com/blockspacer/cmake_helper_utils_conan/blob/master/cmake/Findcmake_helper_utils.cmake

Make sure you use `Debug` build.

include-what-you-use (IWYU) is a project intended to optimise includes.

It will calculate the required headers and add / remove includes as appropriate.

For details, see: [https://include-what-you-use.org/](https://include-what-you-use.org/)

CODESTYLE: use `// IWYU pragma: associated` in C++ source files.

NOTE: Read about IWYU Pragmas: [https://github.com/include-what-you-use/include-what-you-use/blob/master/docs/IWYUPragmas.md](https://github.com/include-what-you-use/include-what-you-use/blob/master/docs/IWYUPragmas.md)

NOTE: don't use "bits/" or "/details/*" includes, add them to mappings file (.imp)

For details, see:

* https://llvm.org/devmtg/2010-11/Silverstein-IncludeWhatYouUse.pdf
* https://github.com/include-what-you-use/include-what-you-use/tree/master/docs
* https://github.com/hdclark/Ygor/blob/master/artifacts/20180225_include-what-you-use/iwyu_how-to.txt

## Build and install to use with sanitizers (example with ASAN)

Conan profile (in `~/.conan/profiles`) must use same CXX ABI as LLVM libs

Example profile `~.conan/profiles/clang_libcpp_asan` can be found below (need to scroll a bit)

```bash
export VERBOSE=1
export CONAN_REVISIONS_ENABLED=1
export CONAN_VERBOSE_TRACEBACK=1
export CONAN_PRINT_RUN_COMMANDS=1
export CONAN_LOGGING_LEVEL=10
export GIT_SSL_NO_VERIFY=true

rm -rf test_package/build/
rm -rf local_build_*

cmake -E time \
  conan install . \
  --install-folder local_build_asan \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  -o llvm_9_installer:include_what_you_use=False \
  -o llvm_9_installer:use_sanitizer="Address;Undefined" \
  --profile clang_libcpp_asan

cmake -E time \
    conan source . \
    --source-folder local_build_asan \
    --install-folder local_build_asan

conan build . \
    --build-folder local_build_asan \
    --source-folder local_build_asan \
    --install-folder local_build_asan

# remove before `conan export-pkg`
(CONAN_REVISIONS_ENABLED=1 \
    conan remove --force llvm_9_installer || true)

conan package . \
    --build-folder local_build_asan \
    --package-folder local_build_asan/package_dir \
    --source-folder local_build_asan \
    --install-folder local_build_asan

conan export-pkg . \
    conan/stable \
    --package-folder local_build_asan/package_dir \
    --settings build_type=Release \
    --force \
    -s llvm_9:build_type=Release \
    -o llvm_9_installer:include_what_you_use=False \
    -o llvm_9_installer:use_sanitizer="Address;Undefined" \
    --profile clang_libcpp_asan

cmake -E time \
  conan test test_package llvm_9_installer/master@conan/stable \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  -o llvm_9_installer:include_what_you_use=False \
  -o llvm_9_installer:use_sanitizer="Address;Undefined" \
  --profile clang_libcpp_asan

rm -rf local_build_asan/package_dir
```

## How to use with sanitizers

Edit `~/.conan/settings.yml` as stated in https://docs.conan.io/en/latest/howtos/sanitizers.html#adding-a-list-of-commonly-used-values

You need to add `sanitizer: [None, Address, Thread, Memory, UndefinedBehavior, AddressUndefinedBehavior]` after each line with `cppstd`.

Edit `~.conan/profiles/clang_libcpp` and add into `[settings]` section:

```bash
compiler.sanitizer=AddressUndefinedBehavior
```

Now set desired sanitizer flags as stated in https://docs.conan.io/en/latest/howtos/sanitizers.html#passing-the-information-to-the-compiler-or-build-system

Example for `-fsanitize=address,undefined` i.e. `AddressUndefinedBehavior`:

```bash
[env]
CXXFLAGS=-DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DADDRESS_SANITIZER=1 -DUNDEFINED_SANITIZER=1 -DUNDEFINED_BEHAVIOR_SANITIZER=1 -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_ASAN=1 -fPIC -fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-wrapv -fno-sanitize-recover=all -fsanitize-recover=unsigned-integer-overflow -fsanitize=address,undefined -shared-libsan -fno-sanitize=nullability-arg -fno-sanitize=nullability-assign -fno-sanitize=nullability-return -fsanitize-trap=undefined -fsanitize=float-divide-by-zero -fno-sanitize=vptr

CFLAGS=-DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DADDRESS_SANITIZER=1 -DUNDEFINED_SANITIZER=1 -DUNDEFINED_BEHAVIOR_SANITIZER=1 -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_ASAN=1 -fPIC -fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-wrapv -fno-sanitize-recover=all -fsanitize-recover=unsigned-integer-overflow -fsanitize=address,undefined -shared-libsan -fno-sanitize=nullability-arg -fno-sanitize=nullability-assign -fno-sanitize=nullability-return -fsanitize-trap=undefined -fsanitize=float-divide-by-zero -fno-sanitize=vptr

LDFLAGS=-fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-sanitize-recover=all -fsanitize-recover=unsigned-integer-overflow -fsanitize=address,undefined -shared-libsan -fno-sanitize=nullability-arg -fno-sanitize=nullability-assign -fno-sanitize=nullability-return -fsanitize-trap=undefined -fsanitize=float-divide-by-zero -fno-sanitize=vptr
```

### About Undefined Behavior Sanitizer

Detects lots of non-memory-related undefined behaviour:

* Signed integer overflow
* Dereferencing null pointers
* Pointer arithmetic overflow
* Dynamic arrays whose size is non-positive

NOTE: Disable custom memory allocation functions (use use_alloc_shim=False). This can hide memory access bugs and prevent the detection of memory access errors.

Edit `~.conan/profiles/{{YOUR_PROFILE_NAME_HERE}}` and add into `[env]` section:

```bash
# see https://github.com/google/sanitizers/wiki/SanitizerCommonFlags
ASAN_OPTIONS=fast_unwind_on_malloc=0:strict_init_order=0:check_initialization_order=false:symbolize=1:handle_segv=0:detect_leaks=1:detect_stack_use_after_return=1:disable_coredump=0:abort_on_error=1

UBSAN_OPTIONS=fast_unwind_on_malloc=0:handle_segv=0:disable_coredump=0:halt_on_error=1:print_stacktrace=1:report_error_type=1

# NOTE: optional, llvm_9_installer able to set UBSAN_SYMBOLIZER_PATH automatically
# make sure that env. var. UBSAN_SYMBOLIZER_PATH points to llvm-symbolizer
# conan package llvm_tools provides llvm-symbolizer
# and prints its path during cmake configure step
# echo $UBSAN_SYMBOLIZER_PATH
# UBSAN_SYMBOLIZER_PATH=$(find ~/.conan/data/llvm_tools/master/conan/stable/package/ -path "*bin/llvm-symbolizer" | head -n 1)

CXXFLAGS=-DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DADDRESS_SANITIZER=1 -DUNDEFINED_SANITIZER=1 -DUNDEFINED_BEHAVIOR_SANITIZER=1 -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_ASAN=1 -fPIC -fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-wrapv -fno-sanitize-recover=all -fsanitize-recover=unsigned-integer-overflow -fsanitize=address,undefined -shared-libsan -fno-sanitize=nullability-arg -fno-sanitize=nullability-assign -fno-sanitize=nullability-return -fsanitize-trap=undefined -fsanitize=float-divide-by-zero -fno-sanitize=vptr

CFLAGS=-DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DADDRESS_SANITIZER=1 -DUNDEFINED_SANITIZER=1 -DUNDEFINED_BEHAVIOR_SANITIZER=1 -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_ASAN=1 -fPIC -fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-wrapv -fno-sanitize-recover=all -fsanitize-recover=unsigned-integer-overflow -fsanitize=address,undefined -shared-libsan -fno-sanitize=nullability-arg -fno-sanitize=nullability-assign -fno-sanitize=nullability-return -fsanitize-trap=undefined -fsanitize=float-divide-by-zero -fno-sanitize=vptr

LDFLAGS=-fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-sanitize-recover=all -fsanitize-recover=unsigned-integer-overflow -fsanitize=address,undefined -shared-libsan -fno-sanitize=nullability-arg -fno-sanitize=nullability-assign -fno-sanitize=nullability-return -fsanitize-trap=undefined -fsanitize=float-divide-by-zero -fno-sanitize=vptr
```

NOTE: Make sure to use clang++ (not ld) as a linker, so that your executable is linked with proper UBSan runtime libraries.

You must build both project and deps with ubsan!

NOTE: Use `_Nonnull` annotation, see [https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html#ubsan-checks](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html#ubsan-checks)

`_Nonnull` annotation requires `-fsanitize=nullability-*`, so we enable them by default:

```bash
  -fsanitize=nullability-arg \
  -fsanitize=nullability-assign \
  -fsanitize=nullability-return \
```

```cpp
Violation of the nonnull Parameter Attribute in C
In the following example, the call to the has_nonnull_argument function breaks the nonnull attribute of the parameter p.

void has_nonnull_argument(__attribute__((nonnull)) int *p) {
     // ...
}
has_nonnull_argument(NULL); // Error: nonnull parameter attribute violation
```

NOTE: Change of options may require rebuild of some deps (`--build=missing`).

Read UBSAN manuals:

* [https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html)
* [https://www.jetbrains.com/help/clion/google-sanitizers.html#UbSanChapter](https://www.jetbrains.com/help/clion/google-sanitizers.html#UbSanChapter)
* [https://github.com/google/sanitizers/wiki](https://github.com/google/sanitizers/wiki)
* [https://www.chromium.org/developers/testing/undefinedbehaviorsanitizer](https://www.chromium.org/developers/testing/undefinedbehaviorsanitizer)

NOTE: you can create blacklist file; see:

* [https://clang.llvm.org/docs/SanitizerSpecialCaseList.html](https://clang.llvm.org/docs/SanitizerSpecialCaseList.html)
* [https://www.mono-project.com/docs/debug+profile/clang/blacklists/](https://www.mono-project.com/docs/debug+profile/clang/blacklists/)

### About Memory Sanitizer

Memory sanitizer (MSan) does check for uninitialized memory accesses

NOTE: MemorySanitizer requires that all program code is instrumented.
This also includes any libraries that the program depends on, even libc. Failing to achieve this may result in false reports.
For the same reason you may need to replace all inline assembly code that writes to memory with a pure C/C++ code.

NOTE: Disable custom memory allocation functions (use use_alloc_shim=False). This can hide memory access bugs and prevent the detection of memory access errors.

Edit `~.conan/profiles/{{YOUR_PROFILE_NAME_HERE}}` and add into `[env]` section:

```bash
# see https://github.com/google/sanitizers/wiki/SanitizerCommonFlags
MSAN_OPTIONS=poison_in_dtor=1:fast_unwind_on_malloc=0:check_initialization_order=false:handle_segv=0:detect_leaks=1:detect_stack_use_after_return=1:disable_coredump=0:abort_on_error=1
# you can also set LSAN_OPTIONS=suppressions=suppr.txt

# NOTE: optional, llvm_9_installer able to set MSAN_SYMBOLIZER_PATH automatically
# make sure that env. var. MSAN_SYMBOLIZER_PATH points to llvm-symbolizer
# conan package llvm_tools provides llvm-symbolizer
# and prints its path during cmake configure step
# echo $MSAN_SYMBOLIZER_PATH
# MSAN_SYMBOLIZER_PATH=$(find ~/.conan/data/llvm_tools/master/conan/stable/package/ -path "*bin/llvm-symbolizer" | head -n 1)

CXXFLAGS=-lpthread -ldl -DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DMEMORY_SANITIZER=1 -DSANITIZE_MEMORY=1 -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_MSAN=1 -fPIC -fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-wrapv -fno-sanitize-recover=all -fsanitize=memory -fsanitize-memory-track-origins

CFLAGS=-lpthread -ldl -DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DMEMORY_SANITIZER=1 -DSANITIZE_MEMORY=1 -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_MSAN=1 -fPIC -fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-wrapv -fno-sanitize-recover=all -fsanitize=memory -fsanitize-memory-track-origins

LDFLAGS=-fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-sanitize-recover=all -fsanitize=memory -fsanitize-memory-track-origins
```

NOTE: you can use -fsanitize-memory-track-origins with "MemoryWithOrigins" sanitizer

If you want MemorySanitizer to work properly and not produce any false positives, you must ensure that all the code in your program and in the libraries it uses is instrumented (i.e. built with `-fsanitize=memory`).
In particular, you would need to link against MSan-instrumented C++ standard library. See: [https://github.com/google/sanitizers/wiki/MemorySanitizerLibcxxHowTo](https://github.com/google/sanitizers/wiki/MemorySanitizerLibcxxHowTo)
You need to re-build both C++ standard library and googletest (and other dependencies) with MemorySanitizer.

Re-build all required projects with MSan-instrumented C++ standard library.

NOTE: re-build some deps with custom MSan-instrumented C++ standard library.
For that you can add to `CMAKE_C_FLAGS` and `CMAKE_CXX_FLAGS`:
`-fsanitize=memory -stdlib=libc++ -L/usr/src/libcxx_msan/lib -lc++abi -I/usr/src/libcxx_msan/include -I/usr/src/libcxx_msan/include/c++/v1` (replace paths to yours).
Usually dependency will have option like `-o *:use_sanitizer="Address;Undefined"` to achieve same effect.

You must build both project and deps with MSan!

NOTE: Change of options may require rebuild of some deps (`--build=missing`).

Read MSAN manuals:

* [https://www.chromium.org/developers/testing/memorysanitizer](https://www.chromium.org/developers/testing/memorysanitizer)
* [https://github.com/google/sanitizers/wiki](https://github.com/google/sanitizers/wiki)
* [https://www.jetbrains.com/help/clion/google-sanitizers.html#MSanChapter](https://www.jetbrains.com/help/clion/google-sanitizers.html#MSanChapter)
* [https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/43308.pdf](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/43308.pdf)

NOTE: `detect_leaks=1` enables Leak Sanitizer; see: [https://sites.google.com/a/chromium.org/dev/developers/testing/leaksanitizer](https://sites.google.com/a/chromium.org/dev/developers/testing/leaksanitizer)

NOTE: you can create blacklist file; see:

* [https://clang.llvm.org/docs/SanitizerSpecialCaseList.html](https://clang.llvm.org/docs/SanitizerSpecialCaseList.html)
* [https://www.mono-project.com/docs/debug+profile/clang/blacklists/](https://www.mono-project.com/docs/debug+profile/clang/blacklists/)

FAQ:

* How to use MemorySanitizer (MSAN) with `syscall(SYS_getrandom, ..., ..., ...)`?
  Use __msan_unpoison:
  ```cpp
  #if defined(__has_feature)
  #if __has_feature(memory_sanitizer)
          /* MemorySanitizer (MSAN) does not support syscall(SYS_getrandom, ..., ..., ...):
           * Use __msan_unpoison to make MSAN understand how many bytes that have been
           * written to ent32.
           *
           * __msan_unpoison does not change the actual memory content, but only MSAN's
           * perception of the memory content.
           *
           * See https://github.com/google/sanitizers/issues/852 ("memory sanitizer: not
           * tracking memory initialization with getrandom") for details.
           */
          __msan_unpoison(ent32, rv);
  #endif
  #endif
  ```

### About Address Sanitizer

NOTE: build with exceptions and rtti disabled; see: [https://bugs.chromium.org/p/chromium/issues/detail?id=832808](https://bugs.chromium.org/p/chromium/issues/detail?id=832808)

NOTE: Address Sanitizer NEVER catches uninitialized memory accesses

For details, see:

* [http://btorpey.github.io/blog/2014/03/27/using-clangs-address-sanitizer/](http://btorpey.github.io/blog/2014/03/27/using-clangs-address-sanitizer/)
* [https://genbattle.bitbucket.io/blog/2018/01/05/Dev-Santa-Claus-Part-1/](https://genbattle.bitbucket.io/blog/2018/01/05/Dev-Santa-Claus-Part-1/)

NOTE: Disable custom memory allocation functions (use use_alloc_shim=False).
This can hide memory access bugs and prevent the detection of memory access errors.

Edit `~.conan/profiles/{{YOUR_PROFILE_NAME_HERE}}` and add into `[env]` section:

```bash
# see https://github.com/google/sanitizers/wiki/AddressSanitizerFlags
ASAN_OPTIONS=fast_unwind_on_malloc=0:strict_init_order=0:check_initialization_order=false:symbolize=1:handle_segv=0:detect_leaks=1:detect_stack_use_after_return=1:disable_coredump=0:abort_on_error=1

UBSAN_OPTIONS=fast_unwind_on_malloc=0:handle_segv=0:disable_coredump=0:halt_on_error=1:print_stacktrace=1:report_error_type=1

# you can also set LSAN_OPTIONS=suppressions=suppr.txt

# NOTE: optional, llvm_9_installer able to set ASAN_SYMBOLIZER_PATH automatically
# make sure that env. var. ASAN_SYMBOLIZER_PATH points to llvm-symbolizer
# conan package llvm_tools provides llvm-symbolizer
# and prints its path during cmake configure step
# echo $ASAN_SYMBOLIZER_PATH
# ASAN_SYMBOLIZER_PATH=$(find ~/.conan/data/llvm_tools/master/conan/stable/package/ -path "*bin/llvm-symbolizer" | head -n 1)

CXXFLAGS=-DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DADDRESS_SANITIZER=1 -DUNDEFINED_SANITIZER=1 -DUNDEFINED_BEHAVIOR_SANITIZER=1 -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_ASAN=1 -fPIC -fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-wrapv -fno-sanitize-recover=all -fsanitize-recover=unsigned-integer-overflow -fsanitize=address,undefined -shared-libsan -fno-sanitize=nullability-arg -fno-sanitize=nullability-assign -fno-sanitize=nullability-return -fsanitize-trap=undefined -fsanitize=float-divide-by-zero -fno-sanitize=vptr

CFLAGS=-DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DADDRESS_SANITIZER=1 -DUNDEFINED_SANITIZER=1 -DUNDEFINED_BEHAVIOR_SANITIZER=1 -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_ASAN=1 -fPIC -fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-wrapv -fno-sanitize-recover=all -fsanitize-recover=unsigned-integer-overflow -fsanitize=address,undefined -shared-libsan -fno-sanitize=nullability-arg -fno-sanitize=nullability-assign -fno-sanitize=nullability-return -fsanitize-trap=undefined -fsanitize=float-divide-by-zero -fno-sanitize=vptr

LDFLAGS=-fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-sanitize-recover=all -fsanitize-recover=unsigned-integer-overflow -fsanitize=address,undefined -shared-libsan -fno-sanitize=nullability-arg -fno-sanitize=nullability-assign -fno-sanitize=nullability-return -fsanitize-trap=undefined -fsanitize=float-divide-by-zero -fno-sanitize=vptr
```

NOTE: Change of options may require rebuild of some deps (`--build=missing`).

Read ASAN manuals:

* [https://clang.llvm.org/docs/AddressSanitizer.html](https://clang.llvm.org/docs/AddressSanitizer.html)
* [https://www.chromium.org/developers/testing/addresssanitizer](https://www.chromium.org/developers/testing/addresssanitizer)
* [https://www.jetbrains.com/help/clion/google-sanitizers.html#AsanChapter](https://www.jetbrains.com/help/clion/google-sanitizers.html#AsanChapter)
* [https://github.com/google/sanitizers/wiki](https://github.com/google/sanitizers/wiki)

NOTE: `detect_leaks=1` enables Leak Sanitizer, see [https://sites.google.com/a/chromium.org/dev/developers/testing/leaksanitizer](https://sites.google.com/a/chromium.org/dev/developers/testing/leaksanitizer)

NOTE: you can create blacklist file; see:

* [https://clang.llvm.org/docs/SanitizerSpecialCaseList.html](https://clang.llvm.org/docs/SanitizerSpecialCaseList.html)
* [https://www.mono-project.com/docs/debug+profile/clang/blacklists/](https://www.mono-project.com/docs/debug+profile/clang/blacklists/)

### About Thread Sanitizer

NOTE: Libc/libstdc++ static linking is not supported.

NOTE: Tsan does not support C++ exceptions.

NOTE: Disable custom memory allocation functions (use use_alloc_shim=False). This can hide memory access bugs and prevent the detection of memory access errors.

NOTE: Non-position-independent executables are not supported.
Therefore, the fsanitize=thread flag will cause Clang to act as though the -fPIE flag had been supplied if compiling without -fPIC, and as though the -pie flag had been supplied if linking an executable.

Edit `~.conan/profiles/{{YOUR_PROFILE_NAME_HERE}}` and add into `[env]` section:

```bash
# see https://github.com/google/sanitizers/wiki/ThreadSanitizerFlags
TSAN_OPTIONS=handle_segv=0:disable_coredump=0:abort_on_error=1:report_thread_leaks=0

# NOTE: optional, llvm_9_installer able to set TSAN_SYMBOLIZER_PATH automatically
# make sure that env. var. TSAN_SYMBOLIZER_PATH points to llvm-symbolizer
# conan package llvm_tools provides llvm-symbolizer
# and prints its path during cmake configure step
# echo $TSAN_SYMBOLIZER_PATH
# TSAN_SYMBOLIZER_PATH=$(find ~/.conan/data/llvm_tools/master/conan/stable/package/ -path "*bin/llvm-symbolizer" | head -n 1)

CXXFLAGS=-lpthread -ldl -DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DTHREAD_SANITIZER=1 -DSANITIZE_THREAD=1 -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_TSAN=1 -fPIC -fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-wrapv -fno-sanitize-recover=all -fsanitize=thread

CFLAGS=-lpthread -ldl -DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DTHREAD_SANITIZER=1 -DSANITIZE_THREAD=1 -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_TSAN=1 -fPIC -fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-wrapv -fno-sanitize-recover=all -fsanitize=thread

LDFLAGS=-fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-sanitize-recover=all -fsanitize=thread
```

NOTE: Change of options may require rebuild of some deps (`--build=missing`).

Read TSAN manuals:

* [https://clang.llvm.org/docs/ThreadSanitizer.html](https://clang.llvm.org/docs/ThreadSanitizer.html)
* [https://github.com/google/sanitizers/wiki/ThreadSanitizerCppManual](https://github.com/google/sanitizers/wiki/ThreadSanitizerCppManual)
* [https://www.jetbrains.com/help/clion/google-sanitizers.html#TSanChapter](https://www.jetbrains.com/help/clion/google-sanitizers.html#TSanChapter)
* [https://www.chromium.org/developers/testing/threadsanitizer-tsan-v2](https://www.chromium.org/developers/testing/threadsanitizer-tsan-v2)

NOTE: ThreadSanitizer generally requires all code to be compiled with -fsanitize=thread.
If some code (e.g. dynamic libraries) is not compiled with the flag, it can lead to false positive race reports, false negative race reports, and/or missed stack frames in reports depending on the nature of non-instrumented code.

NOTE: you can create blacklist file; see:

* [https://clang.llvm.org/docs/SanitizerSpecialCaseList.html](https://clang.llvm.org/docs/SanitizerSpecialCaseList.html)
* [https://www.mono-project.com/docs/debug+profile/clang/blacklists/](https://www.mono-project.com/docs/debug+profile/clang/blacklists/)

## For contributors - Test libc++ support

Run that test manually before pull request.

Export conan package to local cache.

Create conan profile `~.conan/profiles/clang_libcpp` (see above)

```bash
export VERBOSE=1
export CONAN_REVISIONS_ENABLED=1
export CONAN_VERBOSE_TRACEBACK=1
export CONAN_PRINT_RUN_COMMANDS=1
export CONAN_LOG_RUN_TO_FILE=1
export CONAN_LOGGING_LEVEL=10
export GIT_SSL_NO_VERIFY=true

rm -rf test_package/build/
rm -rf local_build_*

cmake -E time \
  conan install . \
  --install-folder local_build_asan \
  -s build_type=Release \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  --profile clang_libcpp \
  -s compiler=clang \
  -s compiler.version=9 \
  -s compiler.libcxx=libc++ \
  --profile clang_libcpp

cmake -E time \
    conan source . \
    --source-folder local_build_asan \
    --install-folder local_build_asan

conan build . \
    --build-folder local_build_asan \
    --source-folder local_build_asan \
    --install-folder local_build_asan

# remove before `conan export-pkg`
(CONAN_REVISIONS_ENABLED=1 \
    conan remove --force llvm_9_installer || true)

conan package . \
    --build-folder local_build_asan \
    --package-folder local_build_asan/package_dir \
    --source-folder local_build_asan \
    --install-folder local_build_asan

conan export-pkg . \
    conan/stable \
    --package-folder local_build_asan/package_dir \
    --settings build_type=Release \
    --force \
    -s build_type=Release \
    -s llvm_9:build_type=Release \
    --profile clang_libcpp \
    -s compiler=clang \
    -s compiler.version=9 \
    -s compiler.libcxx=libc++ \
    --profile clang_libcpp

rm -rf test_package_libcpp/build/
cmake -E time \
  conan test test_package_libcpp llvm_9_installer/master@conan/stable \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  --profile clang_libcpp \
  -s compiler=clang \
  -s compiler.version=9 \
  -s compiler.libcxx=libc++
```

Example for sanitized builds:

```
cmake -E time \
  conan test test_package_libcpp llvm_9_installer/master@conan/stable \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  -o llvm_9_installer:include_what_you_use=False \
  -o llvm_9_installer:use_sanitizer="Address;Undefined" \
  --profile clang_libcpp_asan \
  -s compiler=clang \
  -s compiler.version=9 \
  -s compiler.libcxx=libc++ \
  -s compiler.sanitizer=AddressUndefinedBehavior
```

## For contributors - Test gcc support

Run that test manually before pull request.

Export conan package to local cache.

Create conan profile `~.conan/profiles/gcc`

```
[settings]
os=Linux
os_build=Linux
arch=x86_64
arch_build=x86_64
compiler=gcc
compiler.version=9
compiler.libcxx=libstdc++
build_type=Release
llvm_9:build_type=Release
[options]
[build_requires]
[env]
```

Note that you may need to change some `llvm_9` options, based on desired configuration.

```bash
export VERBOSE=1
export CONAN_REVISIONS_ENABLED=1
export CONAN_VERBOSE_TRACEBACK=1
export CONAN_PRINT_RUN_COMMANDS=1
export CONAN_LOG_RUN_TO_FILE=1
export CONAN_LOGGING_LEVEL=10
export GIT_SSL_NO_VERIFY=true

rm -rf test_package_gcc/build/

cmake -E time \
  conan test test_package_gcc llvm_9_installer/master@conan/stable \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  --profile gcc
```

## For contributors - Test ASAN support

Run that test manually before pull request.

Export conan package to local cache.

Build and export llvm conan package with `-o llvm_9:use_sanitizer="Address;Undefined"`

Create conan profile `~.conan/profiles/clang_libcpp_asan`:

```
[settings]
# We are building in Ubuntu Linux

os_build=Linux
os=Linux
arch_build=x86_64
arch=x86_64

compiler=clang
compiler.version=9
compiler.libcxx=libc++

# enable sanitizer
compiler.sanitizer=AddressUndefinedBehavior

build_type=Debug
llvm_9:build_type=Release

[options]
llvm_9_installer:include_what_you_use=False
llvm_9_installer:compile_with_clang=True
llvm_9_installer:link_libcxx=True
llvm_9:include_what_you_use=False
llvm_9:use_sanitizer="Address;Undefined"

[build_requires]
cmake_installer/3.15.5@conan/stable
llvm_9_installer/master@conan/stable

[env]
ASAN_OPTIONS=fast_unwind_on_malloc=0:strict_init_order=0:check_initialization_order=false:symbolize=1:handle_segv=0:detect_leaks=1:detect_stack_use_after_return=1:disable_coredump=0:abort_on_error=1

UBSAN_OPTIONS=fast_unwind_on_malloc=0:handle_segv=0:disable_coredump=0:halt_on_error=1:print_stacktrace=1:report_error_type=1

CXXFLAGS=-DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DADDRESS_SANITIZER=1 -DUNDEFINED_SANITIZER=1 -DUNDEFINED_BEHAVIOR_SANITIZER=1 -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_ASAN=1 -fPIC -fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-wrapv -fno-sanitize-recover=all -fsanitize-recover=unsigned-integer-overflow -fsanitize=address,undefined -shared-libsan -fno-sanitize=nullability-arg -fno-sanitize=nullability-assign -fno-sanitize=nullability-return -fsanitize-trap=undefined -fsanitize=float-divide-by-zero -fno-sanitize=vptr

CFLAGS=-DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DADDRESS_SANITIZER=1 -DUNDEFINED_SANITIZER=1 -DUNDEFINED_BEHAVIOR_SANITIZER=1 -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_ASAN=1 -fPIC -fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-wrapv -fno-sanitize-recover=all -fsanitize-recover=unsigned-integer-overflow -fsanitize=address,undefined -shared-libsan -fno-sanitize=nullability-arg -fno-sanitize=nullability-assign -fno-sanitize=nullability-return -fsanitize-trap=undefined -fsanitize=float-divide-by-zero -fno-sanitize=vptr

LDFLAGS=-fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-sanitize-recover=all -fsanitize-recover=unsigned-integer-overflow -fsanitize=address,undefined -shared-libsan -fno-sanitize=nullability-arg -fno-sanitize=nullability-assign -fno-sanitize=nullability-return -fsanitize-trap=undefined -fsanitize=float-divide-by-zero -fno-sanitize=vptr
```

Note that you may need to change some `llvm_9` options, based on desired configuration.

```bash
export VERBOSE=1
export CONAN_REVISIONS_ENABLED=1
export CONAN_VERBOSE_TRACEBACK=1
export CONAN_PRINT_RUN_COMMANDS=1
export CONAN_LOG_RUN_TO_FILE=1
export CONAN_LOGGING_LEVEL=10
export GIT_SSL_NO_VERIFY=true

conan create . \
  conan/stable \
  -s build_type=Release \
  --profile clang_libcpp_asan \
  -s llvm_9:build_type=Release \
  -o llvm_9_installer:include_what_you_use=False \
  -o llvm_9_installer:use_sanitizer="Address;Undefined"

rm -rf test_package_sanitize/build/

# NOTE: Must FAIL (!!!) with sanitizer error
# NOTE: If changed to TEST_SANITIZER='san_test_skip' Must pass without error
TEST_SANITIZER='asan_test_use_after_free' \
  cmake -E time \
    conan test test_package_sanitize llvm_9_installer/master@conan/stable \
    -s build_type=Debug \
    -s llvm_9:build_type=Release \
    -o llvm_9_installer:include_what_you_use=False \
    -o llvm_9_installer:use_sanitizer="Address;Undefined" \
    --profile clang_libcpp_asan
```

## For contributors - Test UBSAN support

Run that test manually before pull request.

Export conan package to local cache.

Build and export llvm conan package with `-o llvm_9:use_sanitizer="Address;Undefined"`

Create conan profile `~.conan/profiles/clang_libcpp_ubsan`:

```
[settings]
# We are building in Ubuntu Linux

os_build=Linux
os=Linux
arch_build=x86_64
arch=x86_64

compiler=clang
compiler.version=9
compiler.libcxx=libc++

# enable sanitizer
compiler.sanitizer=AddressUndefinedBehavior

build_type=Debug
llvm_9:build_type=Release

[options]
llvm_9_installer:include_what_you_use=False
llvm_9_installer:compile_with_clang=True
llvm_9_installer:link_libcxx=True
llvm_9:include_what_you_use=False
llvm_9:use_sanitizer="Address;Undefined"

[build_requires]
cmake_installer/3.15.5@conan/stable
llvm_9_installer/master@conan/stable

[env]
ASAN_OPTIONS=fast_unwind_on_malloc=0:strict_init_order=0:check_initialization_order=false:symbolize=1:handle_segv=0:detect_leaks=1:detect_stack_use_after_return=1:disable_coredump=0:abort_on_error=1

UBSAN_OPTIONS=fast_unwind_on_malloc=0:handle_segv=0:disable_coredump=0:halt_on_error=1:print_stacktrace=1:report_error_type=1

CFLAGS=-DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DUNDEFINED_SANITIZER=1 -DUNDEFINED_BEHAVIOR_SANITIZER=1 -DADDRESS_SANITIZER=1 -fsanitize=address,undefined -fno-exceptions -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_ASAN=1 -fuse-ld=lld -stdlib=libc++ -lc++ -lc++abi -lunwind

CXXFLAGS=-DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DUNDEFINED_SANITIZER=1 -DUNDEFINED_BEHAVIOR_SANITIZER=1 -DADDRESS_SANITIZER=1 -fsanitize=address,undefined -fno-exceptions -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_ASAN=1 -fuse-ld=lld -stdlib=libc++ -lc++ -lc++abi -lunwind

LDFLAGS=-fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-sanitize-recover=all -fsanitize-recover=unsigned-integer-overflow -fsanitize=address,undefined -shared-libsan -fno-sanitize=nullability-arg -fno-sanitize=nullability-assign -fno-sanitize=nullability-return -fsanitize-trap=undefined -fsanitize=float-divide-by-zero -fno-sanitize=vptr
```

Note that you may need to change some `llvm_9` options, based on desired configuration.

```bash
export VERBOSE=1
export CONAN_REVISIONS_ENABLED=1
export CONAN_VERBOSE_TRACEBACK=1
export CONAN_PRINT_RUN_COMMANDS=1
export CONAN_LOG_RUN_TO_FILE=1
export CONAN_LOGGING_LEVEL=10
export GIT_SSL_NO_VERIFY=true

conan create . \
  conan/stable \
  -s build_type=Release \
  --profile clang_libcpp_ubsan \
  -s llvm_9:build_type=Release \
  -o llvm_9_installer:include_what_you_use=False \
  -o llvm_9_installer:use_sanitizer="Address;Undefined"

rm -rf test_package_sanitize/build/

# NOTE: Must FAIL (!!!) with sanitizer error
# NOTE: If changed to TEST_SANITIZER='san_test_skip' Must pass without error
TEST_SANITIZER='ubsan_test_signed_overflow' \
  cmake -E time \
    conan test test_package_sanitize llvm_9_installer/master@conan/stable \
    -s build_type=Debug \
    -s llvm_9:build_type=Release \
    -o llvm_9_installer:include_what_you_use=False \
    -o llvm_9_installer:use_sanitizer="Address;Undefined" \
    --profile clang_libcpp_ubsan
```

Now you can build and export llvm conan package with desired options

## For contributors - Test TSAN support

Run that test manually before pull request.

Export conan package to local cache.

Build and export llvm conan package with `-o llvm_9:use_sanitizer="Thread"`

Create conan profile `~.conan/profiles/clang_libcpp_tsan`:

```
[settings]
# We are building in Ubuntu Linux

os_build=Linux
os=Linux
arch_build=x86_64
arch=x86_64

compiler=clang
compiler.version=9
compiler.libcxx=libc++

# enable sanitizer
compiler.sanitizer=Thread

build_type=Debug
llvm_9:build_type=Release

[options]
llvm_9_installer:include_what_you_use=False
llvm_9_installer:compile_with_clang=True
llvm_9_installer:link_libcxx=True
llvm_9:include_what_you_use=False
llvm_9:use_sanitizer="Thread"

[build_requires]
cmake_installer/3.15.5@conan/stable
llvm_9_installer/master@conan/stable

[env]
TSAN_OPTIONS=handle_segv=0:disable_coredump=0:abort_on_error=1:report_thread_leaks=0

CXXFLAGS=-lpthread -ldl -DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DTHREAD_SANITIZER=1 -DSANITIZE_THREAD=1 -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_TSAN=1 -fPIC -fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-wrapv -fno-sanitize-recover=all -fsanitize=thread

CFLAGS=-lpthread -ldl -DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DTHREAD_SANITIZER=1 -DSANITIZE_THREAD=1 -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_TSAN=1 -fPIC -fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-wrapv -fno-sanitize-recover=all -fsanitize=thread

LDFLAGS=-fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-sanitize-recover=all -fsanitize=thread
```

Note that you may need to change some `llvm_9` options, based on desired configuration.

```bash
export VERBOSE=1
export CONAN_REVISIONS_ENABLED=1
export CONAN_VERBOSE_TRACEBACK=1
export CONAN_PRINT_RUN_COMMANDS=1
export CONAN_LOG_RUN_TO_FILE=1
export CONAN_LOGGING_LEVEL=10
export GIT_SSL_NO_VERIFY=true

conan create . \
  conan/stable \
  -s build_type=Release \
  --profile clang_libcpp_tsan \
  -s llvm_9:build_type=Release \
  -o llvm_9_installer:include_what_you_use=False \
  -o llvm_9_installer:use_sanitizer="Thread"

rm -rf test_package_sanitize/build/

# NOTE: Must FAIL (!!!) with sanitizer error
# NOTE: If changed to TEST_SANITIZER='san_test_skip' Must pass without error
TEST_SANITIZER='tsan_test_race' \
  cmake -E time \
    conan test test_package_sanitize llvm_9_installer/master@conan/stable \
    -s build_type=Debug \
    -s llvm_9:build_type=Release \
    -o llvm_9_installer:include_what_you_use=False \
    -o llvm_9_installer:use_sanitizer="Thread" \
    --profile clang_libcpp_tsan
```

Now you can build and export llvm conan package with desired options

## For contributors - Test MSAN support

Run that test manually before pull request.

Export conan package to local cache.

Build and export llvm conan package with `-o llvm_9:use_sanitizer="MemoryWithOrigins"`

Create conan profile `~.conan/profiles/clang_libcpp_msan`:

```
[settings]
# We are building in Ubuntu Linux

os_build=Linux
os=Linux
arch_build=x86_64
arch=x86_64

compiler=clang
compiler.version=9
compiler.libcxx=libc++

# enable sanitizer
compiler.sanitizer=Memory

build_type=Debug
llvm_9:build_type=Release

[options]
llvm_9_installer:include_what_you_use=False
llvm_9_installer:compile_with_clang=True
llvm_9_installer:link_libcxx=True
llvm_9:include_what_you_use=False
llvm_9:use_sanitizer="MemoryWithOrigins"

[build_requires]
cmake_installer/3.15.5@conan/stable
llvm_9_installer/master@conan/stable

[env]
MSAN_OPTIONS=poison_in_dtor=1:fast_unwind_on_malloc=0:check_initialization_order=false:handle_segv=0:detect_leaks=1:detect_stack_use_after_return=1:disable_coredump=0:abort_on_error=1

CXXFLAGS=-lpthread -ldl -DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DMEMORY_SANITIZER=1 -DSANITIZE_MEMORY=1 -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_MSAN=1 -fPIC -fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-wrapv -fno-sanitize-recover=all -fsanitize=memory -fsanitize-memory-track-origins

CFLAGS=-lpthread -ldl -DMEMORY_TOOL_REPLACES_ALLOCATOR=1 -D_FORTIFY_SOURCE=0 -DMEMORY_SANITIZER=1 -DSANITIZE_MEMORY=1 -DBOOST_EXCEPTION_DISABLE=1 -DBOOST_NO_EXCEPTIONS=1 -DBOOST_USE_MSAN=1 -fPIC -fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-wrapv -fno-sanitize-recover=all -fsanitize=memory -fsanitize-memory-track-origins

LDFLAGS=-fno-optimize-sibling-calls -fno-omit-frame-pointer -fno-stack-protector -fno-sanitize-recover=all -fsanitize=memory -fsanitize-memory-track-origins
```

NOTE: you can use -fsanitize-memory-track-origins with "MemoryWithOrigins" sanitizer

Note that you may need to change some `llvm_9` options, based on desired configuration.

```bash
export VERBOSE=1
export CONAN_REVISIONS_ENABLED=1
export CONAN_VERBOSE_TRACEBACK=1
export CONAN_PRINT_RUN_COMMANDS=1
export CONAN_LOG_RUN_TO_FILE=1
export CONAN_LOGGING_LEVEL=10
export GIT_SSL_NO_VERIFY=true

conan create . \
  conan/stable \
  -s build_type=Release \
  --profile clang_libcpp_msan \
  -s llvm_9:build_type=Release \
  -o llvm_9_installer:include_what_you_use=False \
  -o llvm_9_installer:use_sanitizer="MemoryWithOrigins"

rm -rf test_package_sanitize/build/

# NOTE: Must FAIL (!!!) with sanitizer error
# NOTE: If changed to TEST_SANITIZER='san_test_skip' Must pass without error
TEST_SANITIZER='msan_test_corruption' \
  cmake -E time \
    conan test test_package_sanitize llvm_9_installer/master@conan/stable \
    -s build_type=Debug \
    -s llvm_9:build_type=Release \
    -o llvm_9_installer:include_what_you_use=False \
    -o llvm_9_installer:use_sanitizer="MemoryWithOrigins" \
    --profile clang_libcpp_msan
```

Now you can build and export llvm conan package with desired options
