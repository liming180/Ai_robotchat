package com.ai.companion.service;

import com.ai.companion.dto.response.AvatarResponse;

public interface AIService {

    /**
     * 生成伴侣头像：代理 Python AI 服务，并把远程图片落盘到本站 /uploads/。
     *
     * <p>任何失败都不抛异常，统一返回 {@code fallback=true} 的降级结果，保证创建伴侣流程不中断。</p>
     */
    AvatarResponse generateAvatar(String personality, String description);
}
