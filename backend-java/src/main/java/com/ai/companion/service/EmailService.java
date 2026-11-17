package com.ai.companion.service;

/**
 * 邮件发送服务。
 *
 * <p>只负责把验证码交付给 SMTP 服务商；验证码的生成、存储与校验仍由认证服务负责。</p>
 */
public interface EmailService {

    /**
     * 发送注册验证码邮件。
     *
     * @param email 收件邮箱
     * @param code 6 位验证码
     * @throws com.ai.companion.exception.EmailSendException 配置缺失或邮件发送失败
     */
    void sendVerificationCode(String email, String code);
}
