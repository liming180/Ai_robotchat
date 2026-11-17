package com.ai.companion.dto.response;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class NoteResponse {
    private String id;
    /** 可为 null：手动笔记允许不关联伴侣。前端按此渲染「记在 XX 名下」或省略 */
    private String companionId;
    /** 非空 = 从对话「存为笔记」，前端据此渲染「AI 生成」标记与来源行 */
    private String conversationId;
    private String content;
    /** 逗号分隔，前端自行 split（P1-4 契约） */
    private String tags;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
