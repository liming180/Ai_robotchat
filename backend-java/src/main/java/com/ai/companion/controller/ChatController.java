package com.ai.companion.controller;

import com.ai.companion.common.Result;
import com.ai.companion.dto.response.ConversationDetailResponse;
import com.ai.companion.dto.response.ConversationResponse;
import com.ai.companion.service.ChatService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/chat")
@RequiredArgsConstructor
@Tag(name = "聊天", description = "聊天相关接口")
public class ChatController {

    private final ChatService chatService;

    @GetMapping("/conversations")
    @Operation(summary = "获取对话列表")
    public Result<List<ConversationResponse>> getConversationList(
            Authentication authentication,
            @RequestParam(required = false) String companionId,
            @RequestParam(defaultValue = "1") Integer page,
            @RequestParam(defaultValue = "20") Integer pageSize
    ) {
        String userId = (String) authentication.getPrincipal();
        List<ConversationResponse> conversations = chatService.getConversationList(userId, companionId, page, pageSize);
        return Result.success("获取成功", conversations);
    }

    @PostMapping("/conversations")
    @Operation(summary = "创建新对话")
    public Result<ConversationResponse> createConversation(
            Authentication authentication,
            @RequestBody Map<String, String> request
    ) {
        String userId = (String) authentication.getPrincipal();
        String companionId = request.get("companionId");
        String title = request.get("title");
        ConversationResponse conversation = chatService.createConversation(userId, companionId, title);
        return Result.success("创建成功", conversation);
    }

    @GetMapping("/conversations/{id}")
    @Operation(summary = "获取对话详情")
    public Result<ConversationDetailResponse> getConversationDetail(
            Authentication authentication,
            @PathVariable String id
    ) {
        String userId = (String) authentication.getPrincipal();
        ConversationDetailResponse conversation = chatService.getConversationDetail(userId, id);
        return Result.success("获取成功", conversation);
    }

    @PostMapping("/conversations/{id}/messages")
    @Operation(summary = "发送消息")
    public Result<Map<String, Object>> sendMessage(
            Authentication authentication,
            @PathVariable String id,
            @RequestBody Map<String, String> request
    ) {
        String userId = (String) authentication.getPrincipal();
        String content = request.get("content");
        Map<String, Object> result = chatService.sendMessage(userId, id, content);
        return Result.success("发送成功", result);
    }

    @DeleteMapping("/conversations/{id}")
    @Operation(summary = "删除对话")
    public Result<Void> deleteConversation(
            Authentication authentication,
            @PathVariable String id
    ) {
        String userId = (String) authentication.getPrincipal();
        chatService.deleteConversation(userId, id);
        return Result.success("删除成功", null);
    }
}
