package com.ai.companion.service;

/**
 * 文件存储服务。
 * 当前实现为本地磁盘；二期可替换为对象存储（OSS / S3），接口不变。
 */
public interface FileService {

    /**
     * 上传 base64 data URL 图片，返回可访问的 URL。
     *
     * @param dataUrl 形如 data:image/jpeg;base64,/9j/4AAQ...
     * @return 可访问的完整 URL
     */
    String upload(String dataUrl);
}
