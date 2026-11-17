package com.ai.companion.service.impl;

import com.ai.companion.exception.EmailSendException;
import com.ai.companion.service.EmailService;
import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.MailException;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Slf4j
@Service
@RequiredArgsConstructor
public class EmailServiceImpl implements EmailService {

    private static final String SEND_FAILED_MESSAGE = "验证码邮件发送失败，请稍后重试";

    private final JavaMailSender mailSender;

    @Value("${spring.mail.host:}")
    private String mailHost;

    @Value("${spring.mail.username:}")
    private String mailUsername;

    @Value("${spring.mail.password:}")
    private String mailPassword;

    @Value("${spring.mail.from:}")
    private String mailFrom;

    @Override
    public void sendVerificationCode(String email, String code) {
        // 个人 QQ 邮箱要求 From 与 SMTP 认证账号一致，不能只配显示昵称。
        String from = StringUtils.hasText(mailFrom) ? mailFrom.trim() : mailUsername.trim();
        if (!StringUtils.hasText(mailHost) || !StringUtils.hasText(mailUsername)
                || !StringUtils.hasText(mailPassword) || !StringUtils.hasText(from)) {
            throw new EmailSendException("邮件服务未配置，请检查 MAIL_HOST、MAIL_USERNAME、MAIL_PASSWORD");
        }

        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, false, "UTF-8");
            helper.setFrom(from);
            helper.setTo(email);
            helper.setSubject("【AI Companion】注册验证码");
            helper.setText("""
                    你好：

                    你正在注册 AI Companion，本次验证码为：%s

                    验证码 5 分钟内有效，请尽快完成注册。
                    请勿将验证码泄露给他人。如果这不是你的操作，请忽略本邮件。
                    """.formatted(code));
            // send 返回才表示 SMTP 已接受；异常直接向上抛，认证服务不会写 Redis。
            mailSender.send(message);
            log.info("注册验证码邮件已提交 SMTP 发送，收件邮箱: {}", email);
        } catch (MessagingException | MailException e) {
            // 对外不暴露 SMTP 地址、账号、授权码或服务商原始错误，详细原因仅留在服务端日志。
            log.error("注册验证码邮件发送失败，收件邮箱: {}", email, e);
            throw new EmailSendException(SEND_FAILED_MESSAGE, e);
        }
    }
}
