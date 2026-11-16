package com.ai.companion.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.List;

/**
 * 8002 RAG-Knowledge-System 调用封装。
 *
 * <p>用途：伴侣删除时按 companionId 反查其绑定的知识库，逐个调用 8002 的 DELETE 端点。
 * 8002 自己会级联清理 MySQL 中的 collections/documents/chunks 行，并 drop Chroma 向量 collection。</p>
 *
 * <p>为什么用独立的短超时 RestTemplate：删除伴侣时我们不希望因为 8002 慢响应把整条删除链路拖死；
 * 连接 2s / 读 3s，超时直接 fail-fast 抛异常给上层（事务还没开启，MySQL 不会有残留）。</p>
 */
@Slf4j
@Service
public class RagClient {

    private final RestTemplate ragRestTemplate;
    private final ObjectMapper objectMapper;

    @Value("${rag.service.url:http://localhost:8002}")
    private String ragServiceUrl;

    public RagClient(@Qualifier("ragRestTemplate") RestTemplate ragRestTemplate,
                     ObjectMapper objectMapper) {
        this.ragRestTemplate = ragRestTemplate;
        this.objectMapper = objectMapper;
    }

    /**
     * 列出某 companionId 绑定的所有知识库 id。
     *
     * <p>对应 8002 的 {@code GET /api/v1/kb/collections?companionId=...&pageSize=100}。
     * 100 是 8002 的 pageSize 硬上限（collections.py 里 le=100），已远超真实使用量
     * （一个伴侣通常绑 1~3 个知识库），不做分页迭代。</p>
     *
     * @throws RuntimeException 8002 不可达 / 5xx / 响应格式异常。fail-fast 是设计意图。
     */
    public List<String> listCollectionIdsByCompanion(String companionId) {
        String url = ragServiceUrl + "/api/v1/kb/collections?companionId=" + companionId + "&page=1&pageSize=100";
        ResponseEntity<String> resp = ragRestTemplate.getForEntity(url, String.class);
        if (!resp.getStatusCode().is2xxSuccessful() || resp.getBody() == null) {
            throw new RuntimeException("8002 list_collections 非 2xx：" + resp.getStatusCode());
        }
        try {
            JsonNode root = objectMapper.readTree(resp.getBody());
            // 8002 响应：{ success, message, data: { items: [...], total, page, pageSize } }，items 每项有 id 字段
            JsonNode items = root.path("data").path("items");
            List<String> ids = new ArrayList<>();
            if (items.isArray()) {
                for (JsonNode it : items) {
                    String id = it.path("id").asText(null);
                    if (id != null && !id.isEmpty()) ids.add(id);
                }
            }
            return ids;
        } catch (Exception e) {
            throw new RuntimeException("8002 list_collections 响应解析失败: " + e.getMessage(), e);
        }
    }

    /**
     * 删除指定知识库。对应 8002 的 {@code DELETE /api/v1/kb/collections/{id}}。
     * 8002 内部会级联清理文档、切片、向量。
     *
     * @throws RuntimeException 8002 不可达 / 非 2xx。
     */
    public void deleteCollection(String collectionId) {
        String url = ragServiceUrl + "/api/v1/kb/collections/" + collectionId;
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        ResponseEntity<String> resp = ragRestTemplate.exchange(
                url, HttpMethod.DELETE, new HttpEntity<>(headers), String.class);
        if (!resp.getStatusCode().is2xxSuccessful()) {
            throw new RuntimeException("8002 delete_collection 非 2xx：" + resp.getStatusCode() + " body=" + resp.getBody());
        }
        log.info("[RagClient] 已删除知识库 {}", collectionId);
    }
}
