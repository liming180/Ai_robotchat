package com.ai.companion.controller;

import com.ai.companion.common.Result;
import com.ai.companion.dto.request.*;
import com.ai.companion.dto.response.AuthResponse;
import com.ai.companion.service.AuthService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
@Tag(name = "认证", description = "认证相关接口")
public class AuthController {

    private final AuthService authService;

    @PostMapping("/send-email-code")
    @Operation(summary = "发送邮箱验证码")
    public Result<Map<String, Object>> sendEmailCode(@Valid @RequestBody SendEmailCodeRequest request) {
        authService.sendEmailCode(request);
        Map<String, Object> data = new HashMap<>();
        data.put("sent", true);
        data.put("expiresIn", 300);
        return Result.success("验证码发送成功", data);
    }

    @PostMapping("/register")
    @Operation(summary = "用户注册")
    public Result<AuthResponse> register(@Valid @RequestBody RegisterRequest request) {
        AuthResponse response = authService.register(request);
        return Result.success("注册成功", response);
    }

    @PostMapping("/login")
    @Operation(summary = "用户登录")
    public Result<AuthResponse> login(@Valid @RequestBody LoginRequest request) {
        AuthResponse response = authService.login(request);
        return Result.success("登录成功", response);
    }

    @PostMapping("/refresh")
    @Operation(summary = "刷新Token")
    public Result<AuthResponse> refreshToken(@Valid @RequestBody RefreshTokenRequest request) {
        AuthResponse response = authService.refreshToken(request);
        return Result.success("刷新成功", response);
    }
}
