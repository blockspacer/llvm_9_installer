# About

This package is useful as a conan `build_requires`

Features:

* builds code using clang-9
* bundles libc++-9 i.e. -stdlib=libc++ -lc++abi -lc++ -lm -lc
* bundles lld as linker i.e. -fuse-ld=lld
* bundles std header files i.e. -I.../include/c++/v1 -I.../include -nostdinc++ -nodefaultlibs
* bundles clang-tidy, scan-build, ccc-analyzer, c++-analyzer, clang-format to analyze source files
* (conan option) can bundle include-what-you-use to analyze #includes of source files
* (conan option) can bundle google-sanitizers: ASAN - memory error detector, MSAN - detects the use of uninitialized memory, TSAN - data race detector, etc.

## Motivation

* Make sure everyone uses same compiler, std headers, linker, libc++, etc.
* Avoid conflicts with system libs, headers, etc.

## How it works

`llvm_9_installer` sets CC, CXX, etc. environment variables similar to https://docs.conan.io/en/latest/systems_cross_building/cross_building.html

Note that `llvm_9_installer` creates environment variables in conanfile.py i.e. `self.env_info.RC = os.path.join(llvm_root, "bin", "llvm-rc")`, etc.

## Before installation

Build and install https://github.com/blockspacer/conan_llvm_9

`llvm_9_installer` is wrapper around `conan_llvm_9`

## Build and install

```bash
CONAN_REVISIONS_ENABLED=1 \
CONAN_VERBOSE_TRACEBACK=1 \
CONAN_PRINT_RUN_COMMANDS=1 \
CONAN_LOGGING_LEVEL=10 \
GIT_SSL_NO_VERIFY=true \
  cmake -E time \
    conan install . \
    --install-folder local_build_iwyu \
    -s build_type=Release \
    -s llvm_9:build_type=Release \
    -o llvm_9_installer:include_what_you_use=True \
    --profile default

CONAN_REVISIONS_ENABLED=1 \
CONAN_VERBOSE_TRACEBACK=1 \
CONAN_PRINT_RUN_COMMANDS=1 \
CONAN_LOGGING_LEVEL=10 \
GIT_SSL_NO_VERIFY=true \
  cmake -E time \
    conan source . \
    --source-folder local_build_iwyu \
    --install-folder local_build_iwyu

CONAN_REVISIONS_ENABLED=1 \
  CONAN_VERBOSE_TRACEBACK=1 \
  CONAN_PRINT_RUN_COMMANDS=1 \
  CONAN_LOGGING_LEVEL=10 \
  GIT_SSL_NO_VERIFY=true \
  conan build . \
    --build-folder local_build_iwyu \
    --source-folder local_build_iwyu \
    --install-folder local_build_iwyu

# remove before `conan export-pkg`
(CONAN_REVISIONS_ENABLED=1 \
    conan remove --force llvm_9_installer || true)

CONAN_REVISIONS_ENABLED=1 \
  CONAN_VERBOSE_TRACEBACK=1 \
  CONAN_PRINT_RUN_COMMANDS=1 \
  CONAN_LOGGING_LEVEL=10 \
  GIT_SSL_NO_VERIFY=true \
  conan package . \
    --build-folder local_build_iwyu \
    --package-folder local_build_iwyu/package_dir \
    --source-folder local_build_iwyu \
    --install-folder local_build_iwyu

CONAN_REVISIONS_ENABLED=1 \
  CONAN_VERBOSE_TRACEBACK=1 \
  CONAN_PRINT_RUN_COMMANDS=1 \
  CONAN_LOGGING_LEVEL=10 \
  GIT_SSL_NO_VERIFY=true \
  conan export-pkg . \
    conan/stable \
    --package-folder local_build_iwyu/package_dir \
    --settings build_type=Release \
    --force \
    -s llvm_9:build_type=Release \
    -o llvm_9_installer:include_what_you_use=True \
    --profile default

cmake -E time \
  conan test test_package llvm_9_installer/master@conan/stable \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  -o llvm_9_installer:include_what_you_use=True \
  --profile default

rm -rf local_build_iwyu/package_dir
```

## Usage

Create conan profile `~.conan/profiles/clang_with_libcpp_installer`:

```bash
[settings]
# We are building in Ubuntu Linux

os_build=Linux
os=Linux
arch_build=x86_64
arch=x86_64

compiler=clang
compiler.version=9
compiler.libcxx=libc++
compiler.sanitizer=None

[options]
llvm_9_installer:include_what_you_use=True

[build_requires]
cmake_installer/3.15.5@conan/stable
llvm_9_installer/master@conan/stable
```

Now you can use `conan create` command with created conan profile:

```bash
conan create . \
  conan/stable \
  -s build_type=Release \
  --profile clang_with_libcpp_installer \
  --build missing
```

Note `--profile clang_with_libcpp_installer` above.

# How to use with sanitizers

Edit `~/.conan/settings.yml` as stated in https://docs.conan.io/en/latest/howtos/sanitizers.html#adding-a-list-of-commonly-used-values

You need to add `sanitizer: [None, Address, Thread, Memory, UndefinedBehavior, AddressUndefinedBehavior]` after each line with `cppstd`.

Edit `~.conan/profiles/clang_with_libcpp_installer` and add into `[settings]` section line below:

```bash
compiler.sanitizer=AddressUndefinedBehavior
```

Now set desired sanitizer flags as stated in https://docs.conan.io/en/latest/howtos/sanitizers.html#passing-the-information-to-the-compiler-or-build-system

Example for `-fsanitize=address,undefined` i.e. `AddressUndefinedBehavior`:

```bash
[env]
CXXFLAGS= \
  -DMEMORY_TOOL_REPLACES_ALLOCATOR=1 \
  -D_FORTIFY_SOURCE=0 \
  -DUNDEFINED_SANITIZER=1 \
  -DUNDEFINED_BEHAVIOR_SANITIZER=1 \
  -g -O0 \
  -fPIC \
  -fno-optimize-sibling-calls \
  -fno-omit-frame-pointer \
  -fno-stack-protector \
  -fno-wrapv \
  -fno-sanitize-recover=all \
  -fsanitize-recover=unsigned-integer-overflow \
  -fsanitize=address,undefined \
  -shared-libsan \
  -fno-sanitize=nullability-arg \
  -fno-sanitize=nullability-assign \
  -fno-sanitize=nullability-return \
  -fsanitize-trap=undefined \
  -fsanitize=float-divide-by-zero \
  -fno-sanitize=vptr

CFLAGS= \
  -DMEMORY_TOOL_REPLACES_ALLOCATOR=1 \
  -D_FORTIFY_SOURCE=0 \
  -DUNDEFINED_SANITIZER=1 \
  -DUNDEFINED_BEHAVIOR_SANITIZER=1 \
  -g -O0 \
  -fPIC \
  -fno-optimize-sibling-calls \
  -fno-omit-frame-pointer \
  -fno-stack-protector \
  -fno-wrapv \
  -fno-sanitize-recover=all \
  -fsanitize-recover=unsigned-integer-overflow \
  -fsanitize=address,undefined \
  -shared-libsan \
  -fno-sanitize=nullability-arg \
  -fno-sanitize=nullability-assign \
  -fno-sanitize=nullability-return \
  -fsanitize-trap=undefined \
  -fsanitize=float-divide-by-zero \
  -fno-sanitize=vptr

LDFLAGS= \
  -fno-optimize-sibling-calls \
  -fno-omit-frame-pointer \
  -fno-stack-protector \
  -fno-sanitize-recover=all \
  -fsanitize-recover=unsigned-integer-overflow \
  -fsanitize=address,undefined \
  -shared-libsan \
  -fno-sanitize=nullability-arg \
  -fno-sanitize=nullability-assign \
  -fno-sanitize=nullability-return \
  -fsanitize-trap=undefined \
  -fsanitize=float-divide-by-zero \
  -fno-sanitize=vptr
```

## How to enable lld

Add `LDFLAGS=-fuse-ld=lld` into your conan profile.
