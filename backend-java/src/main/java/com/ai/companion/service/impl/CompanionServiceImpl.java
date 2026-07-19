package com.ai.companion.service.impl;

import com.ai.companion.dto.request.CreateCompanionRequest;
import com.ai.companion.dto.response.CompanionResponse;
import com.ai.companion.entity.Companion;
import com.ai.companion.entity.UserCompanion;
import com.ai.companion.mapper.CompanionMapper;
import com.ai.companion.mapper.UserCompanionMapper;
import com.ai.companion.service.CompanionService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class CompanionServiceImpl implements CompanionService {

    private final CompanionMapper companionMapper;
    private final UserCompanionMapper userCompanionMapper;

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
                        companion.getCreatedAt()
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
                companion.getCreatedAt()
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
                companion.getCreatedAt()
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
}
