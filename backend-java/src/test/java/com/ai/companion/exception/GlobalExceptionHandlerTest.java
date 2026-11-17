package com.ai.companion.exception;

import com.ai.companion.common.Result;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class GlobalExceptionHandlerTest {

    @Test
    void 邮件发送失败返回503业务错误() {
        Result<?> result = new GlobalExceptionHandler()
                .handleEmailSendException(new EmailSendException("验证码邮件发送失败，请稍后重试"));

        assertEquals(503, result.getCode());
        assertEquals("验证码邮件发送失败，请稍后重试", result.getMessage());
    }
}
