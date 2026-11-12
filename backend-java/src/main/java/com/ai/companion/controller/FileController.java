package com.ai.companion.controller;

import com.ai.companion.common.Result;
import com.ai.companion.service.FileService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/uploads")
@RequiredArgsConstructor
@Tag(name = "文件", description = "图片上传相关接口")
public class FileController {

    private final FileService fileService;

    @PostMapping
    @Operation(summary = "上传图片", description = "接收 base64 data URL，保存后返回可访问 URL")
    public Result<Map<String, Object>> upload(@RequestBody Map<String, String> request) {
        String url = fileService.upload(request.get("dataUrl"));

        Map<String, Object> data = new HashMap<>();
        data.put("url", url);
        return Result.success("上传成功", data);
    }
}
