package com.ai.companion.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class CreateCompanionRequest {
    @NotBlank(message = "名字不能为空")
    private String name;

    private String avatar;

    private String description;

    private String category;

    private String personality;

    private String systemPrompt;

    private String tags;
}
