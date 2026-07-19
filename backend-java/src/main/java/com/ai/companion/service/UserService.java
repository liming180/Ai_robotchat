package com.ai.companion.service;

import com.ai.companion.dto.response.AuthResponse;

public interface UserService {
    AuthResponse.UserInfo getCurrentUser(String userId);
    AuthResponse.UserInfo updateCurrentUser(String userId, String name, String avatar);
}
