package com.ai.companion.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("message")
public class Message {
    @TableId(type = IdType.ASSIGN_UUID)
    private String id;

    private String conversationId;

    private String role;

    private String content;

    /** 图片 URL 的 JSON 数组字符串（如 ["http://localhost:8080/uploads/2026-11/a.jpg"]）。无图时为 null。 */
    private String images;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableLogic
    private Integer deleted;
}
