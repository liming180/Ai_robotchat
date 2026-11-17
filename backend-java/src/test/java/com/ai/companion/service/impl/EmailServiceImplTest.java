package com.ai.companion.service.impl;

import com.ai.companion.exception.EmailSendException;
import jakarta.mail.Session;
import jakarta.mail.internet.MimeMessage;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mail.MailSendException;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Properties;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class EmailServiceImplTest {

    @Mock
    private JavaMailSender mailSender;

    private EmailServiceImpl emailService;

    @BeforeEach
    void setUp() {
        emailService = new EmailServiceImpl(mailSender);
        ReflectionTestUtils.setField(emailService, "mailHost", "smtp.qq.com");
        ReflectionTestUtils.setField(emailService, "mailUsername", "sender@qq.com");
        ReflectionTestUtils.setField(emailService, "mailPassword", "test-only-not-a-real-secret");
        ReflectionTestUtils.setField(emailService, "mailFrom", "");
    }

    @Test
    void 发送注册验证码时发件人回退到认证账号且正文写明用途和有效期() throws Exception {
        MimeMessage message = new MimeMessage(Session.getInstance(new Properties()));
        when(mailSender.createMimeMessage()).thenReturn(message);

        emailService.sendVerificationCode("receiver@example.com", "654321");

        ArgumentCaptor<MimeMessage> captor = ArgumentCaptor.forClass(MimeMessage.class);
        verify(mailSender).send(captor.capture());
        MimeMessage sent = captor.getValue();
        assertEquals("sender@qq.com", sent.getFrom()[0].toString());
        assertEquals("receiver@example.com", sent.getAllRecipients()[0].toString());
        assertEquals("【AI Companion】注册验证码", sent.getSubject());
        String content = (String) sent.getContent();
        assertTrue(content.contains("注册 AI Companion"));
        assertTrue(content.contains("654321"));
        assertTrue(content.contains("5 分钟内有效"));
    }

    @Test
    void 发件人配置存在时优先使用配置值() throws Exception {
        ReflectionTestUtils.setField(emailService, "mailFrom", "sender@qq.com");
        MimeMessage message = new MimeMessage(Session.getInstance(new Properties()));
        when(mailSender.createMimeMessage()).thenReturn(message);

        emailService.sendVerificationCode("receiver@example.com", "123456");

        ArgumentCaptor<MimeMessage> captor = ArgumentCaptor.forClass(MimeMessage.class);
        verify(mailSender).send(captor.capture());
        assertEquals("sender@qq.com", captor.getValue().getFrom()[0].toString());
    }

    @Test
    void 缺少SMTP配置时不尝试发送并明确报错() {
        ReflectionTestUtils.setField(emailService, "mailPassword", "");

        EmailSendException exception = assertThrows(EmailSendException.class,
                () -> emailService.sendVerificationCode("receiver@example.com", "123456"));
        assertTrue(exception.getMessage().contains("邮件服务未配置"));
        verify(mailSender, never()).send(any(MimeMessage.class));
    }

    @Test
    void SMTP失败时抛出业务异常且不向前端泄露原始错误() {
        when(mailSender.createMimeMessage()).thenReturn(new MimeMessage(Session.getInstance(new Properties())));
        doThrow(new MailSendException("smtp internal detail")).when(mailSender).send(any(MimeMessage.class));

        EmailSendException exception = assertThrows(EmailSendException.class,
                () -> emailService.sendVerificationCode("receiver@example.com", "123456"));
        assertEquals("验证码邮件发送失败，请稍后重试", exception.getMessage());
        assertFalse(exception.getMessage().contains("smtp internal detail"));
    }
}
