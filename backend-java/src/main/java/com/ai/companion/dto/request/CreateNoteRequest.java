package com.ai.companion.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class CreateNoteRequest {

    /** 记在哪个伴侣名下。必须是存在的伴侣（含预置），否则 400「伴侣不存在」。 */
    @NotBlank(message = "伴侣 ID 不能为空")
    private String companionId;

    @NotBlank(message = "笔记内容不能为空")
    private String content;

    /** 逗号分隔，与 companion.tags 同一口径；可空。 */
    @Size(max = 500, message = "标签总长度不能超过 500 个字符")
    private String tags;
}
