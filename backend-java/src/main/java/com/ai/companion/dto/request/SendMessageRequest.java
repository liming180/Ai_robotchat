package com.ai.companion.dto.request;

import lombok.Data;

/**
 * 发送消息请求体。
 *
 * <p>流式聊天（前端直连 Python）结束后，由前端调用本接口把 user / assistant 两条消息落库，
 * 此时传 {@code generate=false}，只落库不调 AI（任务四 P0-5 方案 A）。
 * 未传时保持旧行为（true：落 user 消息 + 同步调 AI 生成 assistant 回复），向后兼容。</p>
 */
@Data
public class SendMessageRequest {

    /** 消息正文，可为空字符串（纯图片消息） */
    private String content;

    /** 角色：user / assistant，默认 user（旧调用方不传时保持原语义） */
    private String role = "user";

    /** 图片 URL 的 JSON 数组字符串，如 ["http://localhost:8081/uploads/2026-11/a.jpg"] */
    private String images;

    /** 是否调用 AI 生成回复，默认 true（向后兼容旧的非流式落库接口） */
    private Boolean generate = true;
}
