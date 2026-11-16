package com.ai.companion.controller;

import com.ai.companion.common.Result;
import com.ai.companion.dto.request.CreateNoteRequest;
import com.ai.companion.dto.request.UpdateNoteRequest;
import com.ai.companion.dto.response.NoteResponse;
import com.ai.companion.service.NoteService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 用户笔记接口。
 *
 * <p>userId 一律从 JWT 主体（{@link Authentication#getPrincipal()}）取，
 * 不接受请求体传入，避免越权。</p>
 */
@RestController
@RequestMapping("/api/v1/notes")
@RequiredArgsConstructor
@Tag(name = "笔记", description = "用户笔记相关接口")
public class NoteController {

    private final NoteService noteService;

    @GetMapping
    @Operation(summary = "获取笔记列表（分页）")
    public Result<Map<String, Object>> listNotes(
            Authentication authentication,
            @RequestParam(required = false) String companionId,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false, defaultValue = "1") Integer page,
            @RequestParam(required = false, defaultValue = "50") Integer pageSize
    ) {
        String userId = (String) authentication.getPrincipal();
        return Result.success("获取成功",
                noteService.listNotes(userId, companionId, keyword, page, pageSize));
    }

    @PostMapping
    @Operation(summary = "新增笔记")
    public Result<NoteResponse> createNote(
            Authentication authentication,
            @Valid @RequestBody CreateNoteRequest request
    ) {
        String userId = (String) authentication.getPrincipal();
        return Result.success("创建成功", noteService.createNote(userId, request));
    }

    @PutMapping("/{id}")
    @Operation(summary = "更新笔记（字段为 null 表示不修改）")
    public Result<NoteResponse> updateNote(
            Authentication authentication,
            @PathVariable String id,
            @RequestBody UpdateNoteRequest request
    ) {
        String userId = (String) authentication.getPrincipal();
        return Result.success("更新成功", noteService.updateNote(userId, id, request));
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除笔记（逻辑删除）")
    public Result<Void> deleteNote(
            Authentication authentication,
            @PathVariable String id
    ) {
        String userId = (String) authentication.getPrincipal();
        noteService.deleteNote(userId, id);
        return Result.success("删除成功", null);
    }
}
