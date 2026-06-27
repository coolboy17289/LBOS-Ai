#ifndef STRINGUTILS_H
#define STRINGUTILS_H

#include <string>
#include <algorithm>
#include <cctype>
#include <locale>

namespace lbos {
namespace utils {

// Trims whitespace from start (in place)
static inline std::string &ltrim(std::string &s) {
    s.erase(s.begin(), std::find_if(s.begin(), s.end(),
        [](unsigned char ch) { return !std::isspace(ch); }));
    return s;
}

// Trims whitespace from end (in place)
static inline std::string &rtrim(std::string &s) {
    s.erase(std::find_if(s.rbegin(), s.rend(),
        [](unsigned char ch) { return !std::isspace(ch); }).base(), s.end());
    return s;
}

// Trims whitespace from both ends (in place)
static inline std::string &trim(std::string &s) {
    return ltrim(rtrim(s));
}

// Returns trimmed copy
static inline std::string trim_copy(const std::string &s) {
    std::string str = s;
    return trim(str);
}

// Converts string to uppercase
static inline std::string to_upper(const std::string &s) {
    std::string result = s;
    std::transform(result.begin(), result.end(), result.begin(),
        [](unsigned char c) { return std::toupper(c); });
    return result;
}

// Converts string to lowercase
static inline std::string to_lower(const std::string &s) {
    std::string result = s;
    std::transform(result.begin(), result.end(), result.begin(),
        [](unsigned char c) { return std::tolower(c); });
    return result;
}

// Simple hash function (djb2) for demonstration
static inline unsigned long hash_string(const std::string &str) {
    unsigned long hash = 5381;
    int c;
    for (size_t i = 0; i < str.length(); i++) {
        c = str[i];
        hash = ((hash << 5) + hash) + c; /* hash * 33 + c */
    }
    return hash;
}

} // namespace utils
} // namespace lbos

#endif // STRINGUTILS_H