package com.ai.companion.mapper;

import com.ai.companion.entity.Note;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Update;

@Mapper
public interface NoteMapper extends BaseMapper<Note> {

    /**
     * 伴侣删除时把其下所有笔记一次性逻辑删。
     *
     * <p>与 {@code ConversationMapper.logicDeleteByCompanionId} 同一写法：
     * {@code @TableLogic} 只在单条 {@code deleteById} 时自动生效，批量 UPDATE 必须显式写
     * {@code deleted = 1}。</p>
     *
     * <p>命中 {@code idx_note_companion_deleted (companion_id, deleted)}，无需回表过滤。</p>
     */
    @Update("UPDATE note SET deleted = 1 WHERE companion_id = #{companionId} AND deleted = 0")
    int logicDeleteByCompanionId(@Param("companionId") String companionId);

    /**
     * 解除笔记与伴侣的关联（companion_id 置 NULL）。
     *
     * <p>必须显式写 UPDATE：MyBatis Plus 的 {@code updateById} 默认跳过 null 字段
     * （{@code FieldStrategy.NOT_NULL}），把实体字段设成 null 不会生成 SET 子句，
     * 前端选「不关联」会静默失效。</p>
     */
    @Update("UPDATE note SET companion_id = NULL WHERE id = #{id} AND deleted = 0")
    int clearCompanionId(@Param("id") String id);
}
