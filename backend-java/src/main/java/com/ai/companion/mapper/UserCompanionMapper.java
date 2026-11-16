package com.ai.companion.mapper;

import com.ai.companion.entity.UserCompanion;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Update;

@Mapper
public interface UserCompanionMapper extends BaseMapper<UserCompanion> {

    /** 伴侣删除时把全部用户对该伴侣的收藏/亲密度关联一次性逻辑删。 */
    @Update("UPDATE user_companion SET deleted = 1 WHERE companion_id = #{companionId} AND deleted = 0")
    int logicDeleteByCompanionId(@Param("companionId") String companionId);
}
