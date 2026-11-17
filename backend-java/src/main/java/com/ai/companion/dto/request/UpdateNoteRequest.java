package com.ai.companion.dto.request;

import jakarta.validation.constraints.Size;
import lombok.Data;

/**
 * 笔记更新请求。所有字段可空，null 表示不修改（对齐 PUT /companions/{id} 的部分更新语义）。
 *
 * <p><b>conversationId 不在本 DTO 内</b>：来源会话是创建时的事实，
 * 编辑笔记不应改写来源（否则「AI 生成」标记可以被随手改成手动，失去意义）。</p>
 */
@Data
public class UpdateNoteRequest {

    private String content;

    /** 逗号分隔；传空串表示清空标签。 */
    @Size(max = 500, message = "标签总长度不能超过 500 个字符")
    private String tags;

    /**
     * 可选：把笔记改归属到另一个伴侣。必须存在，否则 400「伴侣不存在」。
     *
     * <p>null = 不修改；<b>空串 = 解除关联</b>（与 tags 「传空串清空」同一口径）。
     * 不这样约定的话，前端选「不关联」时无法与「不修改」区分。</p>
     */
    private String companionId;
}
