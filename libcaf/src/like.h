#ifndef LIKE_H
#define LIKE_H

#include <string>
#include <ctime>

class Like {
public:
    const std::string commit_hash;   
    const std::string user;          
    const std::time_t timestamp;  
    const std::optional<std::string> prev_like;  

    Like(const std::string& commit_hash, const std::string& user, std::time_t timestamp, const std::optional<std::string>& prev_like = std::nullopt): commit_hash(commit_hash), user(user), timestamp(timestamp), prev_like(prev_like) {}
};
#endif