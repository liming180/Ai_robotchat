package com.ai.companion.controller;

import com.ai.companion.common.Result;
import com.ai.companion.service.AIService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/ai")
@RequiredArgsConstructor
@Tag(name = "AI", description = "AI相关接口")
public class AIController {

    private final AIService aiService;

    @PostMapping("/generate-avatar")
    @Operation(summary = "AI生成头像")
    public Result<Map<String, Object>> generateAvatar(
            Authentication authentication,
            @RequestBody Map<String, String> request
    ) {
        String personality = request.get("personality");
        String description = request.get("description");
        String avatarUrl = aiService.generateAvatar(personality, description);
        
        Map<String, Object> data = new HashMap<>();
        data.put("avatarUrl", avatarUrl);
        
        return Result.success("生成成功", data);
    }
}
