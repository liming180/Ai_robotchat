package com.ai.companion.service;

import com.ai.companion.dto.request.*;
import com.ai.companion.dto.response.AuthResponse;

public interface AuthService {
    /**
     * 发送邮箱验证码。
     *
     * @return mock 模式下返回固定验证码（供本地联调直接使用）；真实模式下返回 null（不外泄验证码）
     */
    String sendEmailCode(SendEmailCodeRequest request);

    AuthResponse register(RegisterRequest request);
    AuthResponse login(LoginRequest request);
    AuthResponse refreshToken(RefreshTokenRequest request);
}
