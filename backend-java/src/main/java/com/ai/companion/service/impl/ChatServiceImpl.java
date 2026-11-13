package com.ai.companion.service.impl;

import com.ai.companion.dto.request.SendMessageRequest;
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

import java.time.LocalDateTime;
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
            msgResponses.add(convertToMessageResponse(msg));
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

    /**
     * 落库一条消息。
     *
     * <p>{@code generate=true}（默认，旧行为）：插入 user 消息后同步调 AI 生成 assistant 回复。
     * <br>{@code generate=false}：只插入请求指定的那一条消息（role 由请求决定），不调 AI。
     * 流式聊天链路（前端直连 Python）在拿到完整回复后，用 generate=false 分别提交
     * user 与 assistant 两条消息，避免重复调用 AI（P0-5 方案 A）。</p>
     */
    @Override
    @Transactional
    public Map<String, Object> sendMessage(String userId, String conversationId, SendMessageRequest request) {
        Conversation conversation = conversationMapper.selectById(conversationId);
        if (conversation == null || !conversation.getUserId().equals(userId)) {
            throw new IllegalArgumentException("对话不存在");
        }

        String content = request.getContent() == null ? "" : request.getContent();
        String images = request.getImages();
        boolean generate = request.getGenerate() == null || request.getGenerate();

        Map<String, Object> result = new HashMap<>();

        // 纯落库模式：只插入请求指定的这一条（role 默认 user），不调 AI。
        if (!generate) {
            String role = "assistant".equals(request.getRole()) ? "assistant" : "user";
            Message message = new Message();
            message.setConversationId(conversationId);
            message.setRole(role);
            message.setContent(content);
            message.setImages(images);
            messageMapper.insert(message);
            touchConversation(conversationId);

            result.put("message", convertToMessageResponse(message));
            return result;
        }

        Message userMessage = new Message();
        userMessage.setConversationId(conversationId);
        userMessage.setRole("user");
        userMessage.setContent(content);
        userMessage.setImages(images);
        messageMapper.insert(userMessage);
        touchConversation(conversationId);

        result.put("userMessage", convertToMessageResponse(userMessage));

        String aiContent = generateAIResponse(conversationId, conversation.getCompanionId(), content);
        Message aiMessage = new Message();
        aiMessage.setConversationId(conversationId);
        aiMessage.setRole("assistant");
        aiMessage.setContent(aiContent);
        messageMapper.insert(aiMessage);
        touchConversation(conversationId);

        companionService.increaseIntimacy(userId, conversation.getCompanionId(), 1);

        result.put("aiMessage", convertToMessageResponse(aiMessage));
        return result;
    }

    /**
     * 插入消息后刷新会话的 updated_at，否则会话列表（按 updated_at 倒序）永远停在学习创建时间，
     * “最近对话”排序与侧栏顺序都不对。
     */
    private void touchConversation(String conversationId) {
        Conversation patch = new Conversation();
        patch.setId(conversationId);
        patch.setUpdatedAt(LocalDateTime.now());
        conversationMapper.updateById(patch);
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
                message.getImages(),
                message.getCreatedAt()
        );
    }
}
