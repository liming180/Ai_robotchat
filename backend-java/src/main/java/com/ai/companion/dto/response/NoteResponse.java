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
    private String companionId;
    private String content;
    /** 逗号分隔，前端自行 split（P1-4 契约） */
    private String tags;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
