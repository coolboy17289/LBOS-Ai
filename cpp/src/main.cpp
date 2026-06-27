#include <iostream>
#include "StringUtils.h"

int main() {
    std::string test = "  Hello, World!  ";
    std::cout << "Original: '" << test << "'" << std::endl;
    std::cout << "Trimmed: '" << lbos::utils::trim_copy(test) << "'" << std::endl;
    std::cout << "Upper: '" << lbos::utils::to_upper(test) << "'" << std::endl;
    std::cout << "Lower: '" << lbos::utils::to_lower(test) << "'" << std::endl;
    std::cout << "Hash: " << lbos::utils::hash_string(test) << std::endl;

    std::string palindrome = "A man, a plan, a canal: Panama";
    std::cout << "Palindrome test (\"" << palindrome << "\"): "
              << (lbos::utils::is_palindrome(palindrome) ? "Yes" : "No") << std::endl;

    return 0;
}