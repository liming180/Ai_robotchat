package com.ai.companion.service.impl;

import com.ai.companion.dto.request.RegisterRequest;
import com.ai.companion.dto.request.SendEmailCodeRequest;
import com.ai.companion.dto.response.AuthResponse;
import com.ai.companion.entity.User;
import com.ai.companion.exception.EmailSendException;
import com.ai.companion.mapper.UserMapper;
import com.ai.companion.service.EmailService;
import com.ai.companion.util.JwtUtil;
import com.ai.companion.util.PasswordUtil;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InOrder;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AuthServiceImplTest {

    private static final String EMAIL = "receiver@example.com";

    @Mock
    private UserMapper userMapper;
    @Mock
    private PasswordUtil passwordUtil;
    @Mock
    private JwtUtil jwtUtil;
    @Mock
    private RedisTemplate<String, Object> redisTemplate;
    @Mock
    private ValueOperations<String, Object> valueOperations;
    @Mock
    private EmailService emailService;

    private AuthServiceImpl authService;

    @BeforeEach
    void setUp() {
        authService = new AuthServiceImpl(userMapper, passwordUtil, jwtUtil, redisTemplate, emailService);
        ReflectionTestUtils.setField(authService, "emailMock", false);
    }

    private void mockInsertAssignsId() {
        doAnswer(invocation -> {
            User user = invocation.getArgument(0);
            user.setId("test-user-id");
            return 1;
        }).when(userMapper).insert(any(User.class));
    }

    private SendEmailCodeRequest sendRequest() {
        SendEmailCodeRequest request = new SendEmailCodeRequest();
        request.setEmail(EMAIL);
        return request;
    }

    @Test
    void 真实模式先发信成功后才写Redis且key和TTL不变() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);

        String result = authService.sendEmailCode(sendRequest());

        assertNull(result);
        InOrder order = inOrder(emailService, redisTemplate, valueOperations);
        order.verify(emailService).sendVerificationCode(eq(EMAIL), argThat(code -> code.matches("\\d{6}")));
        order.verify(redisTemplate).opsForValue();
        order.verify(valueOperations).set(eq("email:code:" + EMAIL),
                argThat(code -> code.toString().matches("\\d{6}")), eq(5L), eq(TimeUnit.MINUTES));
    }

    @Test
    void SMTP失败时不写Redis并继续抛业务异常() {
        doThrow(new EmailSendException("验证码邮件发送失败，请稍后重试"))
                .when(emailService).sendVerificationCode(eq(EMAIL), anyString());

        assertThrows(EmailSendException.class, () -> authService.sendEmailCode(sendRequest()));

        verify(redisTemplate, never()).opsForValue();
        verify(valueOperations, never()).set(anyString(), any(), anyLong(), any());
    }

    @Test
    void SMTP配置缺失时认证流程不写Redis() {
        JavaMailSender mailSender = mock(JavaMailSender.class);
        EmailServiceImpl unconfiguredEmailService = new EmailServiceImpl(mailSender);
        ReflectionTestUtils.setField(unconfiguredEmailService, "mailHost", "");
        ReflectionTestUtils.setField(unconfiguredEmailService, "mailUsername", "");
        ReflectionTestUtils.setField(unconfiguredEmailService, "mailPassword", "");
        ReflectionTestUtils.setField(unconfiguredEmailService, "mailFrom", "");
        AuthServiceImpl unconfiguredAuthService = new AuthServiceImpl(
                userMapper, passwordUtil, jwtUtil, redisTemplate, unconfiguredEmailService);
        ReflectionTestUtils.setField(unconfiguredAuthService, "emailMock", false);

        assertThrows(EmailSendException.class, () -> unconfiguredAuthService.sendEmailCode(sendRequest()));

        verify(mailSender, never()).send(any(jakarta.mail.internet.MimeMessage.class));
        verify(redisTemplate, never()).opsForValue();
    }

    @Test
    void mock模式保持固定码进程内存储且能完成注册() {
        ReflectionTestUtils.setField(authService, "emailMock", true);
        RegisterRequest request = new RegisterRequest();
        request.setEmail(EMAIL);
        request.setName("测试用户");
        request.setPassword("password123");
        request.setCode(authService.sendEmailCode(sendRequest()));

        when(userMapper.selectCount(any())).thenReturn(0L);
        when(passwordUtil.encode("password123")).thenReturn("encoded-password");
        when(jwtUtil.generateAccessToken(anyString(), eq(EMAIL))).thenReturn("access-token");
        when(jwtUtil.generateRefreshToken(anyString())).thenReturn("refresh-token");
        mockInsertAssignsId();

        AuthResponse response = authService.register(request);

        assertEquals("123456", request.getCode());
        assertEquals("access-token", response.getAccessToken());
        assertEquals("refresh-token", response.getRefreshToken());
        assertEquals(EMAIL, response.getUser().getEmail());
        verify(emailService, never()).sendVerificationCode(anyString(), anyString());
        verify(redisTemplate, never()).opsForValue();
        verify(redisTemplate, never()).delete(anyString());
        verify(userMapper).insert(argThat(user -> "encoded-password".equals(user.getPassword())));
    }

    @Test
    void 真实模式注册仍从原Rediskey读取验证码并在成功后删除() {
        AtomicReference<String> code = new AtomicReference<>();
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        doAnswer(invocation -> {
            code.set(invocation.getArgument(1));
            return null;
        }).when(valueOperations).set(eq("email:code:" + EMAIL), any(), eq(5L), eq(TimeUnit.MINUTES));
        authService.sendEmailCode(sendRequest());

        when(valueOperations.get("email:code:" + EMAIL)).thenReturn(code.get());
        when(userMapper.selectCount(any())).thenReturn(0L);
        when(passwordUtil.encode("password123")).thenReturn("encoded-password");
        when(jwtUtil.generateAccessToken(anyString(), eq(EMAIL))).thenReturn("access-token");
        when(jwtUtil.generateRefreshToken(anyString())).thenReturn("refresh-token");
        mockInsertAssignsId();

        RegisterRequest request = new RegisterRequest();
        request.setEmail(EMAIL);
        request.setCode(code.get());
        request.setName("测试用户");
        request.setPassword("password123");
        AuthResponse response = authService.register(request);

        assertEquals("access-token", response.getAccessToken());
        verify(redisTemplate).delete("email:code:" + EMAIL);
    }
}
