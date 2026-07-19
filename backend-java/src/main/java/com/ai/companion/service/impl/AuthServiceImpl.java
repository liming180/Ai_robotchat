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
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.Random;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserMapper userMapper;
    private final PasswordUtil passwordUtil;
    private final JwtUtil jwtUtil;
    private final RedisTemplate<String, Object> redisTemplate;

    @Override
    public void sendEmailCode(SendEmailCodeRequest request) {
        String code = String.format("%06d", new Random().nextInt(1000000));
        redisTemplate.opsForValue().set("email:code:" + request.getEmail(), code, 5, TimeUnit.MINUTES);
        System.out.println("Email code sent to " + request.getEmail() + ": " + code);
    }

    @Override
    public AuthResponse register(RegisterRequest request) {
        String storedCode = (String) redisTemplate.opsForValue().get("email:code:" + request.getEmail());
        if (storedCode == null || !storedCode.equals(request.getCode())) {
            throw new IllegalArgumentException("验证码无效或已过期");
        }

        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(User::getEmail, request.getEmail());
        if (userMapper.selectCount(wrapper) > 0) {
            throw new IllegalArgumentException("该邮箱已被注册");
        }

        User user = new User();
        user.setEmail(request.getEmail());
        user.setName(request.getName());
        user.setPassword(passwordUtil.encode(request.getPassword()));
        userMapper.insert(user);

        redisTemplate.delete("email:code:" + request.getEmail());

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
}
