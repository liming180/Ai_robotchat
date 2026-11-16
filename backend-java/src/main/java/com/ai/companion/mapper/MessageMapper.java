package com.ai.companion.mapper;

import com.ai.companion.entity.Message;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface MessageMapper extends BaseMapper<Message> {

    /**
     * 按会话 id 集合批量逻辑删消息。
     *
     * <p>用 {@code <foreach>} 拼 IN 列表；会话数通常 &lt; 100，IN 不会撑爆 SQL。
     * 若 list 为空，调用方应避免调用此方法（空 IN 是非法 SQL）。</p>
     */
    @Update({
            "<script>",
            "UPDATE message SET deleted = 1",
            "WHERE deleted = 0 AND conversation_id IN",
            "<foreach item='cid' collection='conversationIds' open='(' separator=',' close=')'>#{cid}</foreach>",
            "</script>"
    })
    int logicDeleteByConversationIds(@Param("conversationIds") List<String> conversationIds);
}
