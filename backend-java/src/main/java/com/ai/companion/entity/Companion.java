package com.ai.companion.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("companion")
public class Companion {
    @TableId(type = IdType.ASSIGN_UUID)
    private String id;

    private String name;

    private String avatar;

    private String description;

    private String category;

    private String personality;

    private String systemPrompt;

    private String tags;

    private String createdBy;

    private Boolean isPreset;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;

    @TableLogic
    private Integer deleted;
}
