package com.ai.companion.service.impl;

import com.ai.companion.dto.response.CompanionResponse;
import com.ai.companion.dto.response.ConversationDetailResponse;
import com.ai.companion.dto.response.ConversationResponse;
import com.ai.companion.entity.*;
import com.ai.companion.mapper.*;
import com.ai.companion.service.ChatService;
import com.ai.companion.service.CompanionService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.util.*;

@Service
public class ChatServiceImpl implements ChatService {

    private final ConversationMapper conversationMapper;
    private final MessageMapper messageMapper;
    private final CompanionMapper companionMapper;
    private final UserCompanionMapper userCompanionMapper;
    private final CompanionService companionService;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    
    @Value("${ai.service.url:http://localhost:5000}")
    private String aiServiceUrl;

    public ChatServiceImpl(ConversationMapper conversationMapper,
                          MessageMapper messageMapper,
                          CompanionMapper companionMapper,
                          UserCompanionMapper userCompanionMapper,
                          CompanionService companionService,
                          RestTemplate restTemplate,
                          ObjectMapper objectMapper) {
        this.conversationMapper = conversationMapper;
        this.messageMapper = messageMapper;
        this.companionMapper = companionMapper;
        this.userCompanionMapper = userCompanionMapper;
        this.companionService = companionService;
        this.restTemplate = restTemplate;
        this.objectMapper = objectMapper;
    }

    @Override
    public List<ConversationResponse> getConversationList(String userId, String companionId, Integer page, Integer pageSize) {
        Page<Conversation> pageParam = new Page<>(page, pageSize);
        LambdaQueryWrapper<Conversation> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Conversation::getUserId, userId);
        if (companionId != null) {
            wrapper.eq(Conversation::getCompanionId, companionId);
        }
        wrapper.orderByDesc(Conversation::getUpdatedAt);

        Page<Conversation> conversationPage = conversationMapper.selectPage(pageParam, wrapper);
        List<ConversationResponse> responses = new ArrayList<>();
        for (Conversation conv : conversationPage.getRecords()) {
            responses.add(new ConversationResponse(
                    conv.getId(),
                    conv.getCompanionId(),
                    conv.getTitle(),
                    conv.getUpdatedAt()
            ));
        }
        return responses;
    }

    @Override
    public ConversationDetailResponse getConversationDetail(String userId, String conversationId) {
        Conversation conversation = conversationMapper.selectById(conversationId);
        if (conversation == null || !conversation.getUserId().equals(userId)) {
            throw new IllegalArgumentException("对话不存在");
        }

        CompanionResponse companion = companionService.getCompanionDetail(userId, conversation.getCompanionId());

        LambdaQueryWrapper<Message> msgWrapper = new LambdaQueryWrapper<>();
        msgWrapper.eq(Message::getConversationId, conversationId);
        msgWrapper.orderByAsc(Message::getCreatedAt);
        List<Message> messages = messageMapper.selectList(msgWrapper);

        List<ConversationDetailResponse.MessageResponse> msgResponses = new ArrayList<>();
        for (Message msg : messages) {
            msgResponses.add(new ConversationDetailResponse.MessageResponse(
                    msg.getId(),
                    msg.getRole(),
                    msg.getContent(),
                    msg.getCreatedAt()
            ));
        }

        return new ConversationDetailResponse(
                conversation.getId(),
                conversation.getTitle(),
                companion,
                msgResponses
        );
    }

    @Override
    @Transactional
    public ConversationResponse createConversation(String userId, String companionId, String title) {
        Companion companion = companionMapper.selectById(companionId);
        if (companion == null) {
            throw new IllegalArgumentException("伴侣不存在");
        }

        Conversation conversation = new Conversation();
        conversation.setUserId(userId);
        conversation.setCompanionId(companionId);
        conversation.setTitle(title != null ? title : "新对话");
        conversationMapper.insert(conversation);

        return new ConversationResponse(
                conversation.getId(),
                conversation.getCompanionId(),
                conversation.getTitle(),
                conversation.getUpdatedAt()
        );
    }

    @Override
    @Transactional
    public Map<String, Object> sendMessage(String userId, String conversationId, String content) {
        Conversation conversation = conversationMapper.selectById(conversationId);
        if (conversation == null || !conversation.getUserId().equals(userId)) {
            throw new IllegalArgumentException("对话不存在");
        }

        Message userMessage = new Message();
        userMessage.setConversationId(conversationId);
        userMessage.setRole("user");
        userMessage.setContent(content);
        messageMapper.insert(userMessage);

        String aiContent = generateAIResponse(conversationId, conversation.getCompanionId(), content);
        Message aiMessage = new Message();
        aiMessage.setConversationId(conversationId);
        aiMessage.setRole("assistant");
        aiMessage.setContent(aiContent);
        messageMapper.insert(aiMessage);

        companionService.increaseIntimacy(userId, conversation.getCompanionId(), 1);

        Map<String, Object> result = new HashMap<>();
        result.put("userMessage", convertToMessageResponse(userMessage));
        result.put("aiMessage", convertToMessageResponse(aiMessage));
        return result;
    }

    @Override
    @Transactional
    public void deleteConversation(String userId, String conversationId) {
        Conversation conversation = conversationMapper.selectById(conversationId);
        if (conversation == null || !conversation.getUserId().equals(userId)) {
            throw new IllegalArgumentException("对话不存在");
        }
        conversationMapper.deleteById(conversationId);

        LambdaQueryWrapper<Message> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Message::getConversationId, conversationId);
        messageMapper.delete(wrapper);
    }

    private String generateAIResponse(String conversationId, String companionId, String userContent) {
        Companion companion = companionMapper.selectById(companionId);
        String systemPrompt = companion != null ? companion.getSystemPrompt() : "你是一个友好的AI助手";
        
        // Get conversation history
        LambdaQueryWrapper<Message> msgWrapper = new LambdaQueryWrapper<>();
        msgWrapper.eq(Message::getConversationId, conversationId);
        msgWrapper.orderByAsc(Message::getCreatedAt);
        List<Message> historyMessages = messageMapper.selectList(msgWrapper);
        
        try {
            // Build request to AI service
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("systemPrompt", systemPrompt);
            
            // Add history messages
            List<Map<String, String>> messages = new ArrayList<>();
            for (Message msg : historyMessages) {
                Map<String, String> msgMap = new HashMap<>();
                msgMap.put("role", msg.getRole());
                msgMap.put("content", msg.getContent());
                messages.add(msgMap);
            }
            requestBody.put("messages", messages);
            requestBody.put("userMessage", userContent);
            
            // Set headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            
            // Call AI service
            String url = aiServiceUrl + "/api/v1/ai/chat";
            ResponseEntity<String> response = restTemplate.postForEntity(url, request, String.class);
            
            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                JsonNode root = objectMapper.readTree(response.getBody());
                if (root.path("success").asBoolean(false)) {
                    JsonNode data = root.path("data");
                    return data.path("content").asText();
                }
            }
        } catch (Exception e) {
            System.err.println("Error calling AI service: " + e.getMessage());
            e.printStackTrace();
        }
        
        // Fallback response
        return "抱歉，AI 服务暂时不可用。我们会尽快修复。";
    }

    private ConversationDetailResponse.MessageResponse convertToMessageResponse(Message message) {
        return new ConversationDetailResponse.MessageResponse(
                message.getId(),
                message.getRole(),
                message.getContent(),
                message.getCreatedAt()
        );
    }
}
