package com.ai.companion.service;

import com.ai.companion.dto.response.ConversationDetailResponse;
import com.ai.companion.dto.response.ConversationResponse;

import java.util.List;
import java.util.Map;

public interface ChatService {
    List<ConversationResponse> getConversationList(String userId, String companionId, Integer page, Integer pageSize);
    ConversationDetailResponse getConversationDetail(String userId, String conversationId);
    ConversationResponse createConversation(String userId, String companionId, String title);
    Map<String, Object> sendMessage(String userId, String conversationId, String content);
    void deleteConversation(String userId, String conversationId);
}
