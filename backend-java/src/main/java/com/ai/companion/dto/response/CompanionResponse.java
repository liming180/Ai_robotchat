package com.ai.companion.dto.response;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class CompanionResponse {
    private String id;
    private String name;
    private String avatar;
    private String description;
    private String category;
    private String personality;
    private String systemPrompt;
    private Boolean isFavorite;
    private Integer intimacy;
    private String tags;
    private LocalDateTime createdAt;
    /** 是否预置伴侣（preset-1~4）。预置伴侣前端不展示编辑/删除入口，后端亦禁止修改/删除。 */
    private Boolean isPreset;
    /** 创建者 userId，'system' 表示系统预置。前端用它与 isPreset 一起控制菜单显隐。 */
    private String createdBy;
}
