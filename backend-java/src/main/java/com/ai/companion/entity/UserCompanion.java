package com.ai.companion.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("user_companion")
public class UserCompanion {
    @TableId(type = IdType.ASSIGN_UUID)
    private String id;

    private String userId;

    private String companionId;

    private Boolean isFavorite;

    private Integer intimacy;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;

    @TableLogic
    private Integer deleted;
}
