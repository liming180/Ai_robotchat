package com.ai.companion.mapper;

import com.ai.companion.entity.Conversation;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface ConversationMapper extends BaseMapper<Conversation> {

    /** 列出某伴侣的全部会话 id（含未删除的）。用于伴侣删除时按 id 批量删消息。 */
    @Select("SELECT id FROM conversation WHERE companion_id = #{companionId} AND deleted = 0")
    List<String> selectIdsByCompanionId(@Param("companionId") String companionId);

    /** 伴侣删除时把其下所有会话一次性逻辑删（@TableLogic 在单条 deleteById 才生效，批量 UPDATE 要显式写）。 */
    @Update("UPDATE conversation SET deleted = 1 WHERE companion_id = #{companionId} AND deleted = 0")
    int logicDeleteByCompanionId(@Param("companionId") String companionId);
}
