#ifndef STRING_UTILS_H
#define STRING_UTILS_H

#include <string>

namespace lbos {
namespace util {

std::string reverse_string(const std::string& input);
bool is_palindrome(const std::string& input);

} // namespace util
} // namespace lbos

#endif // STRING_UTILS_H