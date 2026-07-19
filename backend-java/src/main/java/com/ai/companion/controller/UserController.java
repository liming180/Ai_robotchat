package com.ai.companion.controller;

import com.ai.companion.common.Result;
import com.ai.companion.dto.response.AuthResponse;
import com.ai.companion.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Tag(name = "用户", description = "用户相关接口")
public class UserController {

    private final UserService userService;

    @GetMapping("/me")
    @Operation(summary = "获取当前用户信息")
    public Result<AuthResponse.UserInfo> getCurrentUser(Authentication authentication) {
        String userId = (String) authentication.getPrincipal();
        AuthResponse.UserInfo user = userService.getCurrentUser(userId);
        return Result.success("获取成功", user);
    }

    @PutMapping("/me")
    @Operation(summary = "更新当前用户信息")
    public Result<AuthResponse.UserInfo> updateCurrentUser(
            Authentication authentication,
            @RequestBody Map<String, String> request
    ) {
        String userId = (String) authentication.getPrincipal();
        String name = request.get("name");
        String avatar = request.get("avatar");
        AuthResponse.UserInfo user = userService.updateCurrentUser(userId, name, avatar);
        return Result.success("更新成功", user);
    }
}
