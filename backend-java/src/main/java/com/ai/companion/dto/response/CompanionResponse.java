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
}
