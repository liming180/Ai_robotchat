package com.ai.companion.service.impl;

import com.ai.companion.service.AIService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AIServiceImpl implements AIService {

    @Override
    public String generateAvatar(String personality, String description) {
        return "https://api.dicebear.com/9.x/adventurer/svg?seed=" + System.currentTimeMillis();
    }
}
