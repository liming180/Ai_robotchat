package com.ai.companion.service;

import com.ai.companion.dto.request.CreateNoteRequest;
import com.ai.companion.dto.request.UpdateNoteRequest;
import com.ai.companion.dto.response.NoteResponse;

import java.util.Map;

public interface NoteService {

    /**
     * 分页查询当前用户的笔记。
     *
     * @param companionId 可选，不传表示全部伴侣
     * @param keyword     可选，对 content 做模糊匹配
     * @return {items: List&lt;NoteResponse&gt;, total, page, pageSize}
     */
    Map<String, Object> listNotes(String userId, String companionId, String keyword, Integer page, Integer pageSize);

    NoteResponse createNote(String userId, CreateNoteRequest request);

    NoteResponse updateNote(String userId, String noteId, UpdateNoteRequest request);

    void deleteNote(String userId, String noteId);
}
