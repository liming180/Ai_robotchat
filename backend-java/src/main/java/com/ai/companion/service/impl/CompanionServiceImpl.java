package com.ai.companion.service.impl;

import com.ai.companion.dto.request.CreateCompanionRequest;
import com.ai.companion.dto.response.CompanionResponse;
import com.ai.companion.entity.Companion;
import com.ai.companion.entity.UserCompanion;
import com.ai.companion.exception.ServiceUnavailableException;
import com.ai.companion.mapper.CompanionMapper;
import com.ai.companion.mapper.ConversationMapper;
import com.ai.companion.mapper.MessageMapper;
import com.ai.companion.mapper.NoteMapper;
import com.ai.companion.mapper.UserCompanionMapper;
import com.ai.companion.service.CompanionService;
import com.ai.companion.service.RagClient;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionTemplate;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class CompanionServiceImpl implements CompanionService {

    private final CompanionMapper companionMapper;
    private final UserCompanionMapper userCompanionMapper;
    private final ConversationMapper conversationMapper;
    private final MessageMapper messageMapper;
    private final NoteMapper noteMapper;
    private final RagClient ragClient;
    /**
     * 用 TransactionTemplate 而不是在 deleteCompanion 上直接加 @Transactional。
     *
     * <p>原因：删除流程需要「先跨服务清 8002，再本地事务删 MySQL」。如果把 @Transactional 加在最外层，
     * 8002 的 HTTP 调用会持有数据库连接与行锁；且自调用 {@code this.xxx()} 不走 Spring 代理，
     * @Transactional 完全不生效。TransactionTemplate 显式划出事务边界，最稳。</p>
     */
    private final TransactionTemplate transactionTemplate;

    @Override
    public List<CompanionResponse> getCompanionList(String userId, String category, String search, Boolean favorite) {
        LambdaQueryWrapper<Companion> wrapper = new LambdaQueryWrapper<>();
        wrapper.and(w -> w.eq(Companion::getIsPreset, true).or().eq(Companion::getCreatedBy, userId));

        if (category != null && !category.isEmpty()) {
            wrapper.eq(Companion::getCategory, category);
        }
        if (search != null && !search.isEmpty()) {
            wrapper.and(w -> w.like(Companion::getName, search)
                    .or().like(Companion::getDescription, search));
        }

        List<Companion> companions = companionMapper.selectList(wrapper);

        LambdaQueryWrapper<UserCompanion> ucWrapper = new LambdaQueryWrapper<>();
        ucWrapper.eq(UserCompanion::getUserId, userId);
        List<UserCompanion> userCompanions = userCompanionMapper.selectList(ucWrapper);
        Map<String, UserCompanion> userCompanionMap = userCompanions.stream()
                .collect(Collectors.toMap(UserCompanion::getCompanionId, uc -> uc));

        List<CompanionResponse> responses = new ArrayList<>();
        for (Companion companion : companions) {
            UserCompanion uc = userCompanionMap.get(companion.getId());
            boolean isFavorite = uc != null && uc.getIsFavorite();
            Integer intimacy = uc != null ? uc.getIntimacy() : 0;

            if (favorite == null || favorite == isFavorite) {
                responses.add(new CompanionResponse(
                        companion.getId(),
                        companion.getName(),
                        companion.getAvatar(),
                        companion.getDescription(),
                        companion.getCategory(),
                        companion.getPersonality(),
                        companion.getSystemPrompt(),
                        isFavorite,
                        intimacy,
                        companion.getTags(),
                        companion.getCreatedAt(),
                        companion.getIsPreset(),
                        companion.getCreatedBy()
                ));
            }
        }

        return responses;
    }

    @Override
    public CompanionResponse getCompanionDetail(String userId, String companionId) {
        Companion companion = companionMapper.selectById(companionId);
        if (companion == null) {
            throw new IllegalArgumentException("伴侣不存在");
        }

        LambdaQueryWrapper<UserCompanion> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(UserCompanion::getUserId, userId);
        wrapper.eq(UserCompanion::getCompanionId, companionId);
        UserCompanion uc = userCompanionMapper.selectOne(wrapper);

        boolean isFavorite = uc != null && uc.getIsFavorite();
        Integer intimacy = uc != null ? uc.getIntimacy() : 0;

        return new CompanionResponse(
                companion.getId(),
                companion.getName(),
                companion.getAvatar(),
                companion.getDescription(),
                companion.getCategory(),
                companion.getPersonality(),
                companion.getSystemPrompt(),
                isFavorite,
                intimacy,
                companion.getTags(),
                companion.getCreatedAt(),
                companion.getIsPreset(),
                companion.getCreatedBy()
        );
    }

    @Override
    @Transactional
    public CompanionResponse createCompanion(String userId, CreateCompanionRequest request) {
        Companion companion = new Companion();
        companion.setName(request.getName());
        companion.setAvatar(request.getAvatar());
        companion.setDescription(request.getDescription());
        companion.setCategory(request.getCategory());
        companion.setPersonality(request.getPersonality());
        companion.setSystemPrompt(request.getSystemPrompt());
        companion.setTags(request.getTags());
        companion.setCreatedBy(userId);
        companion.setIsPreset(false);
        companionMapper.insert(companion);

        UserCompanion uc = new UserCompanion();
        uc.setUserId(userId);
        uc.setCompanionId(companion.getId());
        uc.setIsFavorite(false);
        uc.setIntimacy(0);
        userCompanionMapper.insert(uc);

        return new CompanionResponse(
                companion.getId(),
                companion.getName(),
                companion.getAvatar(),
                companion.getDescription(),
                companion.getCategory(),
                companion.getPersonality(),
                companion.getSystemPrompt(),
                false,
                0,
                companion.getTags(),
                companion.getCreatedAt(),
                companion.getIsPreset(),
                companion.getCreatedBy()
        );
    }

    @Override
    public CompanionResponse updateCompanion(String userId, String companionId, CreateCompanionRequest request) {
        Companion companion = companionMapper.selectById(companionId);
        if (companion == null) {
            throw new IllegalArgumentException("伴侣不存在");
        }
        if (!userId.equals(companion.getCreatedBy()) || Boolean.TRUE.equals(companion.getIsPreset())) {
            throw new IllegalArgumentException("无权修改该伴侣");
        }

        if (request.getName() != null) companion.setName(request.getName());
        if (request.getAvatar() != null) companion.setAvatar(request.getAvatar());
        if (request.getDescription() != null) companion.setDescription(request.getDescription());
        if (request.getCategory() != null) companion.setCategory(request.getCategory());
        if (request.getPersonality() != null) companion.setPersonality(request.getPersonality());
        if (request.getSystemPrompt() != null) companion.setSystemPrompt(request.getSystemPrompt());
        if (request.getTags() != null) companion.setTags(request.getTags());

        companionMapper.updateById(companion);
        return getCompanionDetail(userId, companionId);
    }

    @Override
    @Transactional
    public Boolean toggleFavorite(String userId, String companionId) {
        LambdaQueryWrapper<UserCompanion> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(UserCompanion::getUserId, userId);
        wrapper.eq(UserCompanion::getCompanionId, companionId);
        UserCompanion uc = userCompanionMapper.selectOne(wrapper);

        boolean newFavorite;
        if (uc == null) {
            uc = new UserCompanion();
            uc.setUserId(userId);
            uc.setCompanionId(companionId);
            uc.setIsFavorite(true);
            uc.setIntimacy(0);
            userCompanionMapper.insert(uc);
            newFavorite = true;
        } else {
            uc.setIsFavorite(!uc.getIsFavorite());
            userCompanionMapper.updateById(uc);
            newFavorite = uc.getIsFavorite();
        }

        return newFavorite;
    }

    @Override
    @Transactional
    public Integer increaseIntimacy(String userId, String companionId, Integer amount) {
        LambdaQueryWrapper<UserCompanion> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(UserCompanion::getUserId, userId);
        wrapper.eq(UserCompanion::getCompanionId, companionId);
        UserCompanion uc = userCompanionMapper.selectOne(wrapper);

        if (uc == null) {
            uc = new UserCompanion();
            uc.setUserId(userId);
            uc.setCompanionId(companionId);
            uc.setIsFavorite(false);
            uc.setIntimacy(amount);
            userCompanionMapper.insert(uc);
        } else {
            uc.setIntimacy(uc.getIntimacy() + amount);
            userCompanionMapper.updateById(uc);
        }

        return uc.getIntimacy();
    }

    /**
     * 删除伴侣实现。注意：本方法故意**不加 @Transactional 注解**在类级别，
     * 而是把跨服务调用（8002）放在事务外，仅 MySQL 部分用 {@link TransactionTemplate} 包起来。
     *
     * <p>原因：跨服务 HTTP 调用持锁会拖长事务，且 8002 的清理动作无法参与本地事务回滚。
     * 把跨服务放到事务外做 fail-fast，事务内只做 MySQL 多表 UPDATE，便于回滚。</p>
     */
    @Override
    public void deleteCompanion(String userId, String companionId) {
        // ---------- 1. 鉴权 + 存在性 + 预置校验 ----------
        Companion companion = companionMapper.selectById(companionId);
        if (companion == null) {
            throw new IllegalArgumentException("伴侣不存在");
        }
        if (Boolean.TRUE.equals(companion.getIsPreset())) {
            throw new IllegalArgumentException("预置伴侣不可删除");
        }
        if (!userId.equals(companion.getCreatedBy())) {
            throw new IllegalArgumentException("无权删除该伴侣");
        }

        // ---------- 2. 先清 8002（fail-fast，失败不动 MySQL） ----------
        List<String> collectionIds;
        try {
            collectionIds = ragClient.listCollectionIdsByCompanion(companionId);
        } catch (Exception e) {
            log.warn("[deleteCompanion] 8002 列表查询失败，中断删除 companion={} err={}", companionId, e.getMessage());
            throw new ServiceUnavailableException("知识库服务不可用，未执行删除：" + e.getMessage(), e);
        }

        for (String cid : collectionIds) {
            try {
                ragClient.deleteCollection(cid);
            } catch (Exception e) {
                log.warn("[deleteCompanion] 8002 删除集合失败 companion={} collection={} err={}", companionId, cid, e.getMessage());
                // 已删的集合不能回滚，但因为是逻辑删除场景、下次重试时列表会跳过已删项，幂等
                throw new ServiceUnavailableException("知识库集合清理失败（已删 " + collectionIds.indexOf(cid) + "/" + collectionIds.size() + "）：" + e.getMessage(), e);
            }
        }

        // ---------- 3. 8002 全清成功，MySQL 本地事务做逻辑删 ----------
        // TransactionTemplate.execute 内部任一步抛异常都会整体回滚，四张表要么全删要么全不删
        transactionTemplate.executeWithoutResult(status -> {
            List<String> conversationIds = conversationMapper.selectIdsByCompanionId(companionId);

            if (!conversationIds.isEmpty()) {
                int msgRows = messageMapper.logicDeleteByConversationIds(conversationIds);
                log.info("[deleteCompanion] 逻辑删 message 行数={}", msgRows);
            }

            int convRows = conversationMapper.logicDeleteByCompanionId(companionId);
            log.info("[deleteCompanion] 逻辑删 conversation 行数={}", convRows);

            // 笔记与会话同口径级联：伴侣删除后不留孤儿笔记（任务十一）
            int noteRows = noteMapper.logicDeleteByCompanionId(companionId);
            log.info("[deleteCompanion] 逻辑删 note 行数={}", noteRows);

            int ucRows = userCompanionMapper.logicDeleteByCompanionId(companionId);
            log.info("[deleteCompanion] 逻辑删 user_companion 行数={}", ucRows);

            // @TableLogic 由 deleteById 自动转 UPDATE ... SET deleted=1
            companionMapper.deleteById(companionId);
        });
    }
}
