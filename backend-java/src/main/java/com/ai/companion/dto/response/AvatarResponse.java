package com.ai.companion.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * AI 头像生成结果。
 *
 * <p>降级必须可观测：只要没走成真实 AI 出图，{@code fallback} 就为 {@code true}
 * 且 {@code fallbackReason} 必有值，前端据此提示用户，不允许静默返回一个看起来正常的 URL。</p>
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AvatarResponse {

    /** 可直接放进 img src 的地址：成功时为本站 /uploads/... 稳定地址，降级时为 dicebear 地址 */
    private String avatarUrl;

    /** true 表示本次没有拿到真实的 AI 生成图（Python 降级 / 代理异常 / 落盘失败） */
    private boolean fallback;

    /** fallback=true 时必有值，说明降级原因 */
    private String fallbackReason;

    /** 真实出图时使用的图像模型（如 cogview-4）；降级时为 null */
    private String model;
}
