package com.ai.companion.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 用户笔记。
 *
 * <p>归属关系：{@code user_id} 是内容所有者（越权判定的唯一依据），
 * {@code companion_id} 表示这条笔记记在哪个伴侣名下（页面显示「来自 XX」），
 * <b>可为 null</b>——手动写的笔记允许不关联任何伴侣。</p>
 *
 * <p>来源区分：{@code conversation_id} 非空表示从对话「存为笔记」过来，
 * 为空表示手动写的。仓库不存 {@code origin} 列，来源完全由这一列推导。</p>
 *
 * <p>删除语义：用户单独删笔记时 {@code @TableLogic} 自动转逻辑删；
 * 删除伴侣时由 {@code NoteMapper.logicDeleteByCompanionId} 在
 * {@code CompanionServiceImpl.deleteCompanion} 的同一事务内级联逻辑删，不留孤儿笔记。
 * 该 SQL 是 {@code WHERE companion_id = #{companionId}}，NULL 永不匹配，
 * 因此不关联伴侣的笔记不会随任何伴侣删除被误删。</p>
 */
@Data
@TableName("note")
public class Note {
    @TableId(type = IdType.ASSIGN_UUID)
    private String id;

    /** 内容所有者，越权校验依据 */
    private String userId;

    /** 记在哪个伴侣名下；伴侣删除时本字段用于级联定位。可为 null（不关联） */
    private String companionId;

    /** 来源会话 id；非空 = 从对话存下来的，为空 = 手动写的 */
    private String conversationId;

    private String content;

    /** 逗号分隔，与 companion.tags 同一口径（P1-4 契约） */
    private String tags;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;

    @TableLogic
    private Integer deleted;
}
