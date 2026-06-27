#include "string_utils.h"
#include <algorithm>

namespace lbos {
namespace util {

std::string reverse_string(const std::string& input) {
    std::string result = input;
    std::reverse(result.begin(), result.end());
    return result;
}

bool is_palindrome(const std::string& input) {
    std::string cleaned;
    for (char c : input) {
        if (std::isalnum(static_cast<unsigned char>(c))) {
            cleaned += std::tolower(static_cast<unsigned char>(c));
        }
    }
    std::string reversed = cleaned;
    std::reverse(reversed.begin(), reversed.end());
    return cleaned == reversed;
}

} // namespace util
} // namespace lbos