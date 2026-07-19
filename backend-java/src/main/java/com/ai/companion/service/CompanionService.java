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
}
