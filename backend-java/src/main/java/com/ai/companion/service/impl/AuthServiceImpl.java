package com.ai.companion.service.impl;

import com.ai.companion.dto.request.*;
import com.ai.companion.dto.response.AuthResponse;
import com.ai.companion.entity.User;
import com.ai.companion.mapper.UserMapper;
import com.ai.companion.service.AuthService;
import com.ai.companion.util.JwtUtil;
import com.ai.companion.util.PasswordUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.Random;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    /** mock 模式固定验证码 */
    private static final String MOCK_CODE = "123456";
    /** 验证码有效期（分钟） */
    private static final long CODE_TTL_MINUTES = 5;

    /**
     * mock 模式下的验证码存储。用进程内 Map 而非 Redis，
     * 这样本地不启动 Redis 也能完整跑通 发送验证码 → 注册 链路。
     */
    private static final Map<String, CodeEntry> MOCK_CODE_STORE = new ConcurrentHashMap<>();

    private final UserMapper userMapper;
    private final PasswordUtil passwordUtil;
    private final JwtUtil jwtUtil;
    private final RedisTemplate<String, Object> redisTemplate;

    /**
     * 验证码 mock 开关。默认 false（真实模式），只有 application.yml 显式配置
     * app.email.mock: true 时才启用，避免部署环境忘记关闭导致验证码恒为 123456。
     */
    @Value("${app.email.mock:false}")
    private boolean emailMock;

    @Override
    public String sendEmailCode(SendEmailCodeRequest request) {
        String email = request.getEmail();

        if (emailMock) {
            MOCK_CODE_STORE.put(email, new CodeEntry(MOCK_CODE,
                    System.currentTimeMillis() + TimeUnit.MINUTES.toMillis(CODE_TTL_MINUTES)));
            System.out.println("[MOCK] 验证码固定为 " + MOCK_CODE + "，邮箱: " + email);
            return MOCK_CODE;
        }

        String code = String.format("%06d", new Random().nextInt(1000000));
        redisTemplate.opsForValue().set(codeKey(email), code, CODE_TTL_MINUTES, TimeUnit.MINUTES);
        // TODO: 接入真实邮件服务后替换此处的控制台输出
        System.out.println("Email code sent to " + email + ": " + code);
        return null;
    }

    @Override
    public AuthResponse register(RegisterRequest request) {
        String email = request.getEmail();
        String storedCode = readCode(email);
        if (storedCode == null || !storedCode.equals(request.getCode())) {
            throw new IllegalArgumentException("验证码无效或已过期");
        }

        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(User::getEmail, email);
        if (userMapper.selectCount(wrapper) > 0) {
            throw new IllegalArgumentException("该邮箱已被注册");
        }

        User user = new User();
        user.setEmail(email);
        user.setName(request.getName());
        user.setPassword(passwordUtil.encode(request.getPassword()));
        userMapper.insert(user);

        clearCode(email);

        return generateAuthResponse(user);
    }

    @Override
    public AuthResponse login(LoginRequest request) {
        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(User::getEmail, request.getEmail());
        User user = userMapper.selectOne(wrapper);

        if (user == null || !passwordUtil.matches(request.getPassword(), user.getPassword())) {
            throw new IllegalArgumentException("邮箱或密码错误");
        }

        return generateAuthResponse(user);
    }

    @Override
    public AuthResponse refreshToken(RefreshTokenRequest request) {
        if (!jwtUtil.validateToken(request.getRefreshToken())) {
            throw new IllegalArgumentException("refreshToken无效或已过期");
        }

        String userId = jwtUtil.getUserIdFromToken(request.getRefreshToken());
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new IllegalArgumentException("用户不存在");
        }

        return generateAuthResponse(user);
    }

    // ── 验证码存取：mock 走内存，真实模式走 Redis ──

    private String readCode(String email) {
        if (emailMock) {
            CodeEntry entry = MOCK_CODE_STORE.get(email);
            if (entry == null) {
                return null;
            }
            if (entry.expireAt < System.currentTimeMillis()) {
                MOCK_CODE_STORE.remove(email);
                return null;
            }
            return entry.code;
        }
        Object value = redisTemplate.opsForValue().get(codeKey(email));
        return value == null ? null : value.toString();
    }

    private void clearCode(String email) {
        if (emailMock) {
            MOCK_CODE_STORE.remove(email);
            return;
        }
        redisTemplate.delete(codeKey(email));
    }

    private String codeKey(String email) {
        return "email:code:" + email;
    }

    private AuthResponse generateAuthResponse(User user) {
        String accessToken = jwtUtil.generateAccessToken(user.getId(), user.getEmail());
        String refreshToken = jwtUtil.generateRefreshToken(user.getId());

        AuthResponse.UserInfo userInfo = new AuthResponse.UserInfo(
                user.getId(),
                user.getEmail(),
                user.getName(),
                user.getAvatar()
        );

        return new AuthResponse(accessToken, refreshToken, "bearer", userInfo);
    }

    /** mock 验证码条目 */
    private record CodeEntry(String code, long expireAt) {
    }
}
