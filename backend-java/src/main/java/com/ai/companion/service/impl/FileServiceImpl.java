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

    /** companion.avatar / user.avatar 等字段长度上限，超出会导致写库失败 */
    private static final int URL_MAX_LENGTH = 500;

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

        // 3. 落盘
        return store(bytes, ext);
    }

    /**
     * 保存已解码的图片字节（供 Java 侧落盘远程头像用）。
     *
     * <p>扩展名优先按文件魔数识别，其次才看 contentType——远程服务声明的类型不可全信；
     * 两者都不在白名单内时拒绝，避免把任意字节当图片存进来。</p>
     */
    @Override
    public String saveImage(byte[] bytes, String contentType) {
        if (bytes == null || bytes.length == 0) {
            throw new IllegalArgumentException("图片数据为空");
        }
        if (bytes.length > maxSize) {
            throw new IllegalArgumentException("图片过大，上限 " + (maxSize / 1024 / 1024) + "MB");
        }

        String ext = detectExtensionByMagic(bytes);
        if (ext == null && contentType != null) {
            ext = ALLOWED_TYPES.get(contentType.split(";")[0].trim().toLowerCase());
        }
        if (ext == null) {
            throw new IllegalArgumentException("不支持的图片类型：" + contentType);
        }
        return store(bytes, ext);
    }

    /** 按文件头识别常见图片格式；无法识别返回 null。 */
    private static String detectExtensionByMagic(byte[] b) {
        if (b.length >= 3 && (b[0] & 0xFF) == 0xFF && (b[1] & 0xFF) == 0xD8 && (b[2] & 0xFF) == 0xFF) {
            return "jpg";
        }
        if (b.length >= 8 && (b[0] & 0xFF) == 0x89 && b[1] == 'P' && b[2] == 'N' && b[3] == 'G') {
            return "png";
        }
        if (b.length >= 6 && b[0] == 'G' && b[1] == 'I' && b[2] == 'F' && b[3] == '8') {
            return "gif";
        }
        if (b.length >= 12 && b[0] == 'R' && b[1] == 'I' && b[2] == 'F' && b[3] == 'F'
                && b[8] == 'W' && b[9] == 'E' && b[10] == 'B' && b[11] == 'P') {
            return "webp";
        }
        return null;
    }

    /** 落盘 {uploadDir}/{yyyy-MM}/{uuid}.{ext} 并返回可访问 URL。 */
    private String store(byte[] bytes, String ext) {
        String month = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyy-MM"));
        String filename = UUID.randomUUID().toString().replace("-", "") + "." + ext;

        // 先算 URL 再落盘：写完之后才发现超长会留下没人引用的孤儿文件
        String base = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        String url = base + "/uploads/" + month + "/" + filename;
        if (url.length() > URL_MAX_LENGTH) {
            throw new IllegalArgumentException("图片地址超出 " + URL_MAX_LENGTH + " 字符上限: " + url.length());
        }

        Path dir = Paths.get(uploadDir).toAbsolutePath().normalize().resolve(month);
        Path target = dir.resolve(filename);
        try {
            Files.createDirectories(dir);
            Files.write(target, bytes);
        } catch (IOException e) {
            log.error("图片落盘失败: {}", target, e);
            throw new IllegalStateException("图片保存失败");
        }

        log.info("图片已保存: {} -> {} ({} bytes)", target, url, bytes.length);
        return url;
    }
}
