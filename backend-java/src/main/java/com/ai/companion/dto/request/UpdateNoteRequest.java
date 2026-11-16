package com.ai.companion.dto.request;

import jakarta.validation.constraints.Size;
import lombok.Data;

/**
 * 笔记更新请求。所有字段可空，null 表示不修改（对齐 PUT /companions/{id} 的部分更新语义）。
 */
@Data
public class UpdateNoteRequest {

    private String content;

    /** 逗号分隔；传空串表示清空标签。 */
    @Size(max = 500, message = "标签总长度不能超过 500 个字符")
    private String tags;

    /** 可选：把笔记改归属到另一个伴侣。必须存在，否则 400「伴侣不存在」。 */
    private String companionId;
}
