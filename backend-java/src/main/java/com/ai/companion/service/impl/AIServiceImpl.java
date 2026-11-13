package com.ai.companion.service.impl;

import com.ai.companion.dto.response.AvatarResponse;
import com.ai.companion.service.AIService;
import com.ai.companion.service.FileService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

/**
 * 头像生成：代理 Python AI 服务，并把远程图片落盘到本站 /uploads/。
 *
 * <p>为什么不纯透传：CogView 返回的是第三方临时直链（带水印、会过期），而
 * {@code companion.avatar} 是持久化字段，直接存直链会导致历史伴侣头像裂图。</p>
 */
@Slf4j
@Service
public class AIServiceImpl implements AIService {

    /** companion.avatar 字段长度上限，超出会写库失败 */
    private static final int AVATAR_URL_MAX_LENGTH = 500;
    private static final String DICEBEAR_BASE = "https://api.dicebear.com/9.x/adventurer/svg?seed=";

    private final RestTemplate avatarRestTemplate;
    private final ObjectMapper objectMapper;
    private final FileService fileService;

    @Value("${ai.service.url:http://localhost:5000}")
    private String aiServiceUrl;

    public AIServiceImpl(@Qualifier("avatarRestTemplate") RestTemplate avatarRestTemplate,
                         ObjectMapper objectMapper,
                         FileService fileService) {
        this.avatarRestTemplate = avatarRestTemplate;
        this.objectMapper = objectMapper;
        this.fileService = fileService;
    }

    @Override
    public AvatarResponse generateAvatar(String personality, String description) {
        try {
            JsonNode data = requestPythonAvatar(personality, description);

            // Python 明确告知降级，或压根没给图 —— 一律按降级处理，绝不把 SVG/占位当成功
            if (data == null) {
                return fallback(personality, "Python 响应缺少 data");
            }
            if (data.path("fallback").asBoolean(false)) {
                return fallback(personality, "Python 降级: " + data.path("fallbackReason").asText("未知原因"));
            }
            String remoteUrl = data.path("avatarUrl").asText("");
            if (remoteUrl.isBlank()) {
                return fallback(personality, "Python 未返回 avatarUrl");
            }

            String localUrl = persistImage(remoteUrl);
            if (localUrl == null) {
                return fallback(personality, "Python 返回的图片无法落盘（SVG 或下载失败）");
            }
            if (localUrl.length() > AVATAR_URL_MAX_LENGTH) {
                return fallback(personality, "落盘地址超出 " + AVATAR_URL_MAX_LENGTH + " 字符");
            }

            return AvatarResponse.builder()
                    .avatarUrl(localUrl)
                    .fallback(false)
                    .model(data.path("model").asText(null))
                    .build();
        } catch (Exception e) {
            // 任何异常都不向上抛：创建伴侣流程依赖这个接口，降级比中断更可取
            log.warn("[avatar] Java 代理生成失败，走降级。原因: {}", e.getMessage(), e);
            return fallback(personality, "代理调用失败: " + e.getClass().getSimpleName());
        }
    }

    /** 调 Python 头像接口，返回响应体里的 data 节点；调用失败抛异常由上层兜底。 */
    private JsonNode requestPythonAvatar(String personality, String description) throws Exception {
        Map<String, String> body = new HashMap<>();
        body.put("personality", personality);
        body.put("description", description);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(new MediaType(MediaType.APPLICATION_JSON, StandardCharsets.UTF_8));
        HttpEntity<Map<String, String>> request = new HttpEntity<>(body, headers);

        String url = aiServiceUrl + "/api/v1/ai/generate-avatar";
        ResponseEntity<String> response = avatarRestTemplate.postForEntity(url, request, String.class);
        if (response.getBody() == null) {
            throw new IllegalStateException("Python 返回空响应");
        }

        JsonNode root = objectMapper.readTree(response.getBody());
        if (!root.path("success").asBoolean(false)) {
            throw new IllegalStateException("Python 返回失败: " + root.path("message").asText(""));
        }
        return root.path("data");
    }

    /**
     * 把远程图片落到本站 /uploads/，返回本地 URL。
     *
     * @return 无法落盘（SVG data URL、下载失败、类型不支持、过大）时返回 null
     */
    private String persistImage(String remoteUrl) {
        try {
            if (remoteUrl.startsWith("data:")) {
                // SVG 不在上传白名单内（且 base64 体积远超 VARCHAR(500)），只接受位图 data URL
                if (!remoteUrl.startsWith("data:image/") || remoteUrl.startsWith("data:image/svg")) {
                    return null;
                }
                int comma = remoteUrl.indexOf(',');
                if (comma < 0) return null;
                String mime = remoteUrl.substring(5, comma).split(";")[0].trim();
                byte[] bytes = Base64.getDecoder().decode(remoteUrl.substring(comma + 1));
                return fileService.saveImage(bytes, mime);
            }

            if (!remoteUrl.startsWith("http://") && !remoteUrl.startsWith("https://")) {
                return null;
            }

            ResponseEntity<byte[]> response = avatarRestTemplate.getForEntity(remoteUrl, byte[].class);
            byte[] bytes = response.getBody();
            if (bytes == null || bytes.length == 0) return null;

            String contentType = response.getHeaders().getContentType() != null
                    ? response.getHeaders().getContentType().toString()
                    : null;
            return fileService.saveImage(bytes, contentType);
        } catch (Exception e) {
            log.warn("[avatar] 图片落盘失败: {} ({})", remoteUrl, e.getMessage());
            return null;
        }
    }

    /**
     * 构造降级结果：dicebear 地址 + 明确原因。
     *
     * <p>seed 刻意用「人设哈希 + 时间戳」而非原始人设文本：中文经 URL 编码后每字膨胀约 9 倍，
     * 长人设会把 URL 撑破 {@code companion.avatar} 的 500 字符上限，让降级路径自己崩掉。</p>
     */
    private AvatarResponse fallback(String personality, String reason) {
        String seed = shortHash(personality) + "-" + System.currentTimeMillis();
        String url = DICEBEAR_BASE + URLEncoder.encode(seed, StandardCharsets.UTF_8);
        if (url.length() > AVATAR_URL_MAX_LENGTH) {
            // 理论上不会发生（seed 已固定短哈希），兜底截断保证一定可入库
            url = DICEBEAR_BASE + System.currentTimeMillis();
        }
        log.info("[avatar] 使用降级头像: 原因={}, url={}", reason, url);
        return AvatarResponse.builder()
                .avatarUrl(url)
                .fallback(true)
                .fallbackReason(reason)
                .build();
    }

    /** 取 SHA-256 前 8 位十六进制，作为人设的稳定短标识。 */
    private static String shortHash(String text) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest((text == null ? "" : text).getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < 4; i++) {
                sb.append(String.format("%02x", digest[i]));
            }
            return sb.toString();
        } catch (Exception e) {
            return Integer.toHexString(text == null ? 0 : text.hashCode());
        }
    }
}
