package com.ai.companion.exception;

/**
 * 下游依赖服务不可用（如 8002 RAG 服务超时/不可达）。
 *
 * <p>映射为 HTTP 502，与「后端自身 500」区分开：前端可据此提示
 * 「知识库服务暂时不可用，伴侣未删除」，而不是笼统的「服务器错误」。</p>
 */
public class ServiceUnavailableException extends RuntimeException {

    public ServiceUnavailableException(String message) {
        super(message);
    }

    public ServiceUnavailableException(String message, Throwable cause) {
        super(message, cause);
    }
}
