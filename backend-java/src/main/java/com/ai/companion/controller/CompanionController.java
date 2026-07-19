package com.ai.companion.controller;

import com.ai.companion.common.Result;
import com.ai.companion.dto.request.CreateCompanionRequest;
import com.ai.companion.dto.response.CompanionResponse;
import com.ai.companion.service.CompanionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/companions")
@RequiredArgsConstructor
@Tag(name = "伴侣", description = "伴侣相关接口")
public class CompanionController {

    private final CompanionService companionService;

    @GetMapping
    @Operation(summary = "获取伴侣列表")
    public Result<List<CompanionResponse>> getCompanionList(
            Authentication authentication,
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String search,
            @RequestParam(required = false) Boolean favorite
    ) {
        String userId = (String) authentication.getPrincipal();
        List<CompanionResponse> companions = companionService.getCompanionList(userId, category, search, favorite);
        return Result.success("获取成功", companions);
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取伴侣详情")
    public Result<CompanionResponse> getCompanionDetail(
            Authentication authentication,
            @PathVariable String id
    ) {
        String userId = (String) authentication.getPrincipal();
        CompanionResponse companion = companionService.getCompanionDetail(userId, id);
        return Result.success("获取成功", companion);
    }

    @PostMapping
    @Operation(summary = "创建自定义伴侣")
    public Result<CompanionResponse> createCompanion(
            Authentication authentication,
            @Valid @RequestBody CreateCompanionRequest request
    ) {
        String userId = (String) authentication.getPrincipal();
        CompanionResponse companion = companionService.createCompanion(userId, request);
        return Result.success("创建成功", companion);
    }

    @PutMapping("/{id}")
    @Operation(summary = "更新伴侣人设")
    public Result<CompanionResponse> updateCompanion(
            Authentication authentication,
            @PathVariable String id,
            @RequestBody CreateCompanionRequest request
    ) {
        String userId = (String) authentication.getPrincipal();
        CompanionResponse companion = companionService.updateCompanion(userId, id, request);
        return Result.success("更新成功", companion);
    }

    @PatchMapping("/{id}/favorite")
    @Operation(summary = "切换收藏状态")
    public Result<Map<String, Object>> toggleFavorite(
            Authentication authentication,
            @PathVariable String id
    ) {
        String userId = (String) authentication.getPrincipal();
        Boolean isFavorite = companionService.toggleFavorite(userId, id);
        Map<String, Object> data = new HashMap<>();
        data.put("isFavorite", isFavorite);
        return Result.success("操作成功", data);
    }

    @PatchMapping("/{id}/intimacy")
    @Operation(summary = "增加亲密度")
    public Result<Map<String, Object>> increaseIntimacy(
            Authentication authentication,
            @PathVariable String id,
            @RequestBody Map<String, Integer> request
    ) {
        String userId = (String) authentication.getPrincipal();
        Integer amount = request.getOrDefault("amount", 1);
        Integer intimacy = companionService.increaseIntimacy(userId, id, amount);
        Map<String, Object> data = new HashMap<>();
        data.put("intimacy", intimacy);
        return Result.success("亲密度增加成功", data);
    }
}
