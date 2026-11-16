package com.ai.companion.service;

import com.ai.companion.dto.request.CreateCompanionRequest;
import com.ai.companion.dto.response.CompanionResponse;

import java.util.List;

public interface CompanionService {
    List<CompanionResponse> getCompanionList(String userId, String category, String search, Boolean favorite);
    CompanionResponse getCompanionDetail(String userId, String companionId);
    CompanionResponse createCompanion(String userId, CreateCompanionRequest request);
    CompanionResponse updateCompanion(String userId, String companionId, CreateCompanionRequest request);
    Boolean toggleFavorite(String userId, String companionId);
    Integer increaseIntimacy(String userId, String companionId, Integer amount);

    /**
     * 删除自定义伴侣（级联：8002 知识库与向量 + MySQL 的 companion/user_companion/conversation/message 行）。
     *
     * <p>fail-fast 顺序：先调 8002 清向量与知识库元数据；全部成功后再开启 MySQL 本地事务做逻辑删。
     * 8002 任一调用失败直接抛 502，MySQL 不动。MySQL 事务回滚时已清空的 8002 数据由调用方重试补偿
     * （下次重试时 8002 列表为空，幂等）。</p>
     *
     * <p>不删的：用户级记忆/情绪（user_memories/user_moods 无 companion_id 列）、uploads/ 下的头像文件
     * （统一由 T-3 二期定时回收）。</p>
     */
    void deleteCompanion(String userId, String companionId);
}
