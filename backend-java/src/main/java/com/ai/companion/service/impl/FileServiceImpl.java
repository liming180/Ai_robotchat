package com.ai.companion.service.impl;

import com.ai.companion.service.FileService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Base64;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
public class FileServiceImpl implements FileService {

    /** 允许的图片 MIME → 扩展名。白名单制，避免任意文件落盘。 */
    private static final Map<String, String> ALLOWED_TYPES = Map.of(
            "image/jpeg", "jpg",
            "image/jpg", "jpg",
            "image/png", "png",
            "image/webp", "webp",
            "image/gif", "gif"
    );

    @Value("${app.upload.dir:./uploads}")
    private String uploadDir;

    @Value("${app.upload.base-url:http://localhost:8080}")
    private String baseUrl;

    @Value("${app.upload.max-size:5242880}")
    private long maxSize;

    @Override
    public String upload(String dataUrl) {
        if (dataUrl == null || dataUrl.isBlank()) {
            throw new IllegalArgumentException("图片数据为空");
        }

        // 1. 拆出 MIME 与 base64 载荷
        int commaIndex = dataUrl.indexOf(',');
        if (!dataUrl.startsWith("data:") || commaIndex < 0) {
            throw new IllegalArgumentException("图片格式不正确，需为 base64 data URL");
        }
        String header = dataUrl.substring(5, commaIndex);
        String payload = dataUrl.substring(commaIndex + 1);

        // header 形如 image/jpeg;base64
        String mime = header.split(";")[0].trim().toLowerCase();
        if (!header.toLowerCase().contains(";base64")) {
            throw new IllegalArgumentException("仅支持 base64 编码的图片");
        }
        String ext = ALLOWED_TYPES.get(mime);
        if (ext == null) {
            throw new IllegalArgumentException("不支持的图片类型：" + mime);
        }

        // 2. 解码并校验大小
        byte[] bytes;
        try {
            bytes = Base64.getDecoder().decode(payload);
        } catch (IllegalArgumentException e) {
            throw new IllegalArgumentException("base64 数据解码失败");
        }
        if (bytes.length == 0) {
            throw new IllegalArgumentException("图片数据为空");
        }
        if (bytes.length > maxSize) {
            throw new IllegalArgumentException("图片过大，上限 " + (maxSize / 1024 / 1024) + "MB");
        }

        // 3. 落盘 {uploadDir}/{yyyy-MM}/{uuid}.{ext}
        String month = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyy-MM"));
        String filename = UUID.randomUUID().toString().replace("-", "") + "." + ext;
        Path dir = Paths.get(uploadDir).toAbsolutePath().normalize().resolve(month);
        Path target = dir.resolve(filename);
        try {
            Files.createDirectories(dir);
            Files.write(target, bytes);
        } catch (IOException e) {
            log.error("图片落盘失败: {}", target, e);
            throw new IllegalStateException("图片保存失败");
        }

        // 4. 拼接 URL（去掉 base-url 末尾斜杠，避免出现双斜杠）
        String base = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        String url = base + "/uploads/" + month + "/" + filename;
        log.info("图片已保存: {} -> {} ({} bytes)", target, url, bytes.length);
        return url;
    }
}
