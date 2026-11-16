package com.ai.companion.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

@Configuration
public class RestTemplateConfig {

    /** 普通业务调用的默认客户端（聊天等），保持无自定义超时。 */
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }

    /**
     * 头像生成专用客户端。
     *
     * <p>CogView 出图本身需 8~10 秒，之后还要下载 1~3MB 的图片字节，因此读超时必须显著大于出图时间，
     * 否则会出现「Java 先判定超时降级，Python 随后才返回真图」的假降级。连接 30s / 读取 60s，
     * 且不与 ChatServiceImpl 共用以免放宽聊天链路的超时。</p>
     */
    @Bean("avatarRestTemplate")
    public RestTemplate avatarRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(30_000);
        factory.setReadTimeout(60_000);
        return new RestTemplate(factory);
    }

    /**
     * 8002 RAG 服务专用客户端。
     *
     * <p>删除伴侣时会按 companionId 列出知识库并逐个 DELETE。这里用短超时（连接 2s / 读 3s）
     * 是刻意的：8002 不可用时我们要 fail-fast（让上层返回 502 并不动 MySQL），
     * 而不是让整条删除链路挂在 HTTP 等待上。</p>
     */
    @Bean("ragRestTemplate")
    public RestTemplate ragRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(2_000);
        factory.setReadTimeout(3_000);
        return new RestTemplate(factory);
    }
}
