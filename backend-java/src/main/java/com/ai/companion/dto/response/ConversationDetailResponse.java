package com.ai.companion.dto.response;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ConversationDetailResponse {
    private String id;
    private String title;
    private CompanionResponse companion;
    private List<MessageResponse> messages;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class MessageResponse {
        private String id;
        private String role;
        private String content;
        /** 图片 URL 的 JSON 数组字符串，由前端 JSON.parse；无图时为 null。 */
        private String images;
        private LocalDateTime createdAt;
    }
}
