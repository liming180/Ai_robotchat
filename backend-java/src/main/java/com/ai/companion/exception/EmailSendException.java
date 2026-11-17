package com.ai.companion.exception;

/**
 * 验证码邮件未成功交付给 SMTP 服务商。
 *
 * <p>调用方必须中断发送成功流程，不能写入可供注册的验证码。</p>
 */
public class EmailSendException extends RuntimeException {

    public EmailSendException(String message) {
        super(message);
    }

    public EmailSendException(String message, Throwable cause) {
        super(message, cause);
    }
}
