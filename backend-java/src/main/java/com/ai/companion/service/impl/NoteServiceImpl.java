package com.ai.companion.service.impl;

import com.ai.companion.dto.request.CreateNoteRequest;
import com.ai.companion.dto.request.UpdateNoteRequest;
import com.ai.companion.dto.response.NoteResponse;
import com.ai.companion.entity.Companion;
import com.ai.companion.entity.Note;
import com.ai.companion.mapper.CompanionMapper;
import com.ai.companion.mapper.NoteMapper;
import com.ai.companion.service.NoteService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 笔记 CRUD。
 *
 * <p><b>归属校验</b>：{@code userId} 一律由 Controller 从 JWT 主体取出传入，不接受请求体。
 * 查不到或不属于当前用户时统一抛「笔记不存在」——不区分「不存在」与「无权」，
 * 避免通过错误文案探测他人笔记是否存在（对齐 Python 记忆接口口径）。</p>
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class NoteServiceImpl implements NoteService {

    /** pageSize 上限，与 8002 的 le=100 习惯一致 */
    private static final int MAX_PAGE_SIZE = 100;

    private final NoteMapper noteMapper;
    private final CompanionMapper companionMapper;

    @Override
    public Map<String, Object> listNotes(String userId, String companionId, String keyword,
                                         Integer page, Integer pageSize) {
        int safePage = (page == null || page < 1) ? 1 : page;
        int safeSize = (pageSize == null || pageSize < 1) ? 50 : Math.min(pageSize, MAX_PAGE_SIZE);

        LambdaQueryWrapper<Note> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Note::getUserId, userId);
        if (StringUtils.hasText(companionId)) {
            wrapper.eq(Note::getCompanionId, companionId);
        }
        if (StringUtils.hasText(keyword)) {
            wrapper.like(Note::getContent, keyword);
        }
        wrapper.orderByDesc(Note::getUpdatedAt);

        Page<Note> notePage = noteMapper.selectPage(new Page<>(safePage, safeSize), wrapper);
        List<NoteResponse> items = notePage.getRecords().stream().map(this::toResponse).toList();

        Map<String, Object> result = new HashMap<>();
        result.put("items", items);
        result.put("total", notePage.getTotal());
        result.put("page", safePage);
        result.put("pageSize", safeSize);
        return result;
    }

    @Override
    public NoteResponse createNote(String userId, CreateNoteRequest request) {
        requireCompanionExists(request.getCompanionId());

        Note note = new Note();
        note.setUserId(userId);
        note.setCompanionId(request.getCompanionId());
        note.setContent(request.getContent());
        note.setTags(request.getTags());
        noteMapper.insert(note);
        return toResponse(note);
    }

    @Override
    public NoteResponse updateNote(String userId, String noteId, UpdateNoteRequest request) {
        Note note = requireOwnedNote(userId, noteId);

        if (request.getCompanionId() != null && !request.getCompanionId().equals(note.getCompanionId())) {
            requireCompanionExists(request.getCompanionId());
            note.setCompanionId(request.getCompanionId());
        }
        if (request.getContent() != null) {
            if (!StringUtils.hasText(request.getContent())) {
                throw new IllegalArgumentException("笔记内容不能为空");
            }
            note.setContent(request.getContent());
        }
        // tags 允许显式传空串以清空标签，所以判断的是 != null 而非 hasText
        if (request.getTags() != null) {
            note.setTags(request.getTags());
        }

        noteMapper.updateById(note);
        return toResponse(note);
    }

    @Override
    public void deleteNote(String userId, String noteId) {
        Note note = requireOwnedNote(userId, noteId);
        // @TableLogic 自动转 UPDATE note SET deleted = 1
        noteMapper.deleteById(note.getId());
        log.info("[deleteNote] 逻辑删笔记 id={} user={}", noteId, userId);
    }

    /**
     * 取笔记并校验归属。
     *
     * <p>不存在与越权使用同一文案「笔记不存在」，防止探测。</p>
     */
    private Note requireOwnedNote(String userId, String noteId) {
        Note note = noteMapper.selectById(noteId);
        if (note == null || !userId.equals(note.getUserId())) {
            throw new IllegalArgumentException("笔记不存在");
        }
        return note;
    }

    /**
     * 校验伴侣存在且未删除。预置伴侣允许（用户可以对预置伴侣记笔记）。
     *
     * <p>{@code selectById} 受 {@code @TableLogic} 约束，已逻辑删除的伴侣查不到。</p>
     */
    private void requireCompanionExists(String companionId) {
        Companion companion = companionMapper.selectById(companionId);
        if (companion == null) {
            throw new IllegalArgumentException("伴侣不存在");
        }
    }

    private NoteResponse toResponse(Note note) {
        return new NoteResponse(
                note.getId(),
                note.getCompanionId(),
                note.getContent(),
                note.getTags(),
                note.getCreatedAt(),
                note.getUpdatedAt()
        );
    }
}
