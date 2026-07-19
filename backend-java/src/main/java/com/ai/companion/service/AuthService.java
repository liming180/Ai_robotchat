package com.ai.companion.service;

import com.ai.companion.dto.request.*;
import com.ai.companion.dto.response.AuthResponse;

public interface AuthService {
    void sendEmailCode(SendEmailCodeRequest request);
    AuthResponse register(RegisterRequest request);
    AuthResponse login(LoginRequest request);
    AuthResponse refreshToken(RefreshTokenRequest request);
}
