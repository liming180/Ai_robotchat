package com.ai.companion.service.impl;

import org.junit.jupiter.api.Test;
import org.springframework.boot.autoconfigure.mail.MailProperties;
import org.springframework.boot.context.properties.bind.Binder;
import org.springframework.boot.env.YamlPropertySourceLoader;
import org.springframework.core.env.PropertySource;
import org.springframework.core.env.StandardEnvironment;
import org.springframework.core.io.ClassPathResource;

import java.io.IOException;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/** 不启动数据库或 Redis，直接验证提交的 application.yml 邮件绑定。 */
class MailConfigurationTest {

    @Test
    void QQ邮箱465显式启用SSL且三项超时均为5000毫秒() throws IOException {
        List<PropertySource<?>> sources = new YamlPropertySourceLoader()
                .load("application", new ClassPathResource("application.yml"));
        StandardEnvironment environment = new StandardEnvironment();
        sources.forEach(source -> environment.getPropertySources().addLast(source));

        MailProperties properties = Binder.get(environment)
                .bind("spring.mail", MailProperties.class)
                .orElseThrow(() -> new AssertionError("缺少 spring.mail 配置"));

        assertEquals("", properties.getHost());
        assertEquals(465, properties.getPort());
        assertEquals("", properties.getUsername());
        assertEquals("", properties.getPassword());
        assertEquals("UTF-8", properties.getDefaultEncoding().name());
        assertEquals("true", properties.getProperties().get("mail.smtp.auth"));
        assertEquals("true", properties.getProperties().get("mail.smtp.ssl.enable"));
        assertEquals("5000", properties.getProperties().get("mail.smtp.connectiontimeout"));
        assertEquals("5000", properties.getProperties().get("mail.smtp.timeout"));
        assertEquals("5000", properties.getProperties().get("mail.smtp.writetimeout"));
    }
}
