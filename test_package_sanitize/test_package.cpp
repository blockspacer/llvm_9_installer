#include <cstdlib>
#include <iostream>
#include <iterator>
#include <exception>
#include <string>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <memory>
#include <vector>
#include <thread>

// __has_include is currently supported by GCC and Clang. However GCC 4.9 may have issues and
// returns 1 for 'defined( __has_include )', while '__has_include' is actually not supported:
// https://gcc.gnu.org/bugzilla/show_bug.cgi?id=63662
#if __has_include(<filesystem>)
#include <filesystem>
#else
#include <experimental/filesystem>
#endif // __has_include

int Global;

static void Thread1() {
  Global = 42;
}

struct foo {
  int a, b;
};

int main(int argc, const char **argv) {
  std::string env_param = std::getenv("TEST_SANITIZER");
  if(env_param.empty()) {
    std::cerr << "Missing env. param: " << "TEST_SANITIZER" << std::endl;
    return EXIT_FAILURE;
  }

  std::cout << "Env. param is: " << env_param << std::endl;
  if (env_param == "san_test_skip") {
    std::cout << "san_test_skip" << std::endl;
  }
  else if (env_param == "asan_test_use_after_free") {
    int *array = new int[100];
    delete [] array;
    int a = array[argc]; // BOOM
    std::cerr << "asan_test_use_after_free: " << a << std::endl;
  }
  else if (env_param == "asan_test_array_bounds") {
    static constexpr size_t N = 10;
    char s[N] = "123456789";
    for (int i = 0; i <= N; i++)
      std::cerr << "asan_test_array_bounds: " <<  s[i] << std::endl;
  }
  else if (env_param == "asan_test_use_after_free") {
    int* s = new int{9};
    delete s;
    std::cerr << "asan_test_use_after_free: " <<  *s << std::endl;
  }
  else if (env_param == "asan_test_double_free") {
    int* s = new int{9};
    delete s;
    delete s; // double-free !
    std::cerr << "asan_test_double_free: " <<  *s << std::endl;
  }
  // Enormous number of possible sources of undefined behavior
  // https://blog.regehr.org/archives/1520
  else if (env_param == "ubsan_test_signed_overflow") {
    int k = std::numeric_limits<int>::max();
    k += argc; // BOOM
    std::cerr << "ubsan_test_signed_overflow: " << k << std::endl;
  }
  else if (env_param == "ubsan_test_zero_div") {
    int k = argc;
    k = k / (k - k); // BOOM
    std::cerr << "ubsan_test_zero_div: " << k << std::endl;
  }
  else if (env_param == "ubsan_test_nullptr_access") {
    foo *k = nullptr;
    int m = k->a; // BOOM
    std::cerr << "ubsan_test_nullptr_access: " << m << std::endl;
  }
  else if (env_param == "tsan_test_race") {
    std::thread t(&Thread1);
    Global = argc;
    t.join();
    std::cerr << "tsan_test_race: " << Global << std::endl;
  }
  else if (env_param == "msan_test_corruption") {
    int* a = new int[10];
    a[5] = 0;
    volatile int b = a[argc];
    if (b)
      printf("xx\n");
    std::cerr << "msan_test_corruption: " << a[1] << std::endl;
  }
  else {
    std::cerr << "Unknown env. param: " << "TEST_SANITIZER" << std::endl;
    return EXIT_FAILURE;
  }

  const std::string str = "Hello world!";
  std::cout << str << std::endl;
  return EXIT_SUCCESS;
}
