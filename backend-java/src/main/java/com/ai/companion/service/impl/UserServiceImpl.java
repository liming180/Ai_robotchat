package com.ai.companion.service.impl;

import com.ai.companion.dto.response.AuthResponse;
import com.ai.companion.entity.User;
import com.ai.companion.mapper.UserMapper;
import com.ai.companion.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;

    @Override
    public AuthResponse.UserInfo getCurrentUser(String userId) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new IllegalArgumentException("用户不存在");
        }
        return new AuthResponse.UserInfo(
                user.getId(),
                user.getEmail(),
                user.getName(),
                user.getAvatar()
        );
    }

    @Override
    public AuthResponse.UserInfo updateCurrentUser(String userId, String name, String avatar) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new IllegalArgumentException("用户不存在");
        }
        if (name != null) {
            user.setName(name);
        }
        if (avatar != null) {
            user.setAvatar(avatar);
        }
        userMapper.updateById(user);
        return new AuthResponse.UserInfo(
                user.getId(),
                user.getEmail(),
                user.getName(),
                user.getAvatar()
        );
    }
}
