<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { api } from '@/lib/api'
import type { CompanionItem, RetrieveResult } from '@/lib/api'

const companions = ref<CompanionItem[]>([])
const collections = ref<{ id: string; name: string }[]>([])
const loading = ref(false)
const result = ref<RetrieveResult | null>(null)

const form = reactive({
  mode: 'companion' as 'companion' | 'collection',
  companionId: '',
  collectionIds: [] as string[],
  query: '',
  topK: 4,
  scoreThreshold: 0,
})

async function search() {
  if (!form.query.trim()) {
    ElMessage.warning('请输入检索问题')
    return
  }
  if (form.mode === 'companion' && !form.companionId) {
    ElMessage.warning('请选择角色')
    return
  }
  if (form.mode === 'collection' && !form.collectionIds.length) {
    ElMessage.warning('请选择知识库')
    return
  }
  loading.value = true
  try {
    result.value = await api.retrieve({
      query: form.query.trim(),
      companionId: form.mode === 'companion' ? form.companionId : undefined,
      collectionIds: form.mode === 'collection' ? form.collectionIds : undefined,
      topK: form.topK,
      scoreThreshold: form.scoreThreshold || undefined,
    })
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '检索失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    companions.value = (await api.listCompanions()).items
  } catch {
    // 角色下拉留空不影响检索调试
  }
  try {
    const data = await api.listCollections({ page: 1, pageSize: 100 })
    collections.value = data.items.map((c) => ({ id: c.id, name: c.name }))
  } catch {
    // 知识库下拉留空
  }
})
</script>

<template>
  <div>
    <el-card shadow="never" class="mb-4">
      <el-form label-position="top" @submit.prevent="search">
        <div class="flex flex-wrap items-end gap-4">
          <el-form-item label="检索范围" class="!mb-0">
            <el-radio-group v-model="form.mode">
              <el-radio-button value="companion">按角色</el-radio-button>
              <el-radio-button value="collection">按知识库</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item v-if="form.mode === 'companion'" label="角色" class="!mb-0">
            <el-select v-model="form.companionId" placeholder="选择角色" class="!w-56">
              <el-option v-for="c in companions" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </el-form-item>
          <el-form-item v-else label="知识库（可多选）" class="!mb-0">
            <el-select
              v-model="form.collectionIds"
              multiple
              collapse-tags
              placeholder="选择知识库"
              class="!w-72"
            >
              <el-option v-for="c in collections" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="topK" class="!mb-0">
            <el-input-number v-model="form.topK" :min="1" :max="20" />
          </el-form-item>
          <el-form-item label="分数阈值" class="!mb-0">
            <el-input-number v-model="form.scoreThreshold" :min="0" :max="1" :step="0.05" />
          </el-form-item>
        </div>
        <div class="mt-4 flex gap-3">
          <el-input
            v-model="form.query"
            placeholder="输入检索问题，验证知识召回效果"
            @keyup.enter="search"
          />
          <el-button type="primary" :loading="loading" @click="search">检 索</el-button>
        </div>
      </el-form>
    </el-card>

    <div v-if="result">
      <p class="mb-3 text-sm text-neutral-400">
        命中 {{ result.chunks.length }} 条 · 耗时 {{ result.elapsedMs }}ms ·
        检索知识库 {{ result.searchedCollections.length }} 个
      </p>
      <el-empty v-if="!result.chunks.length" description="没有命中任何切片" />
      <el-card
        v-for="(chunk, i) in result.chunks"
        :key="i"
        shadow="never"
        class="mb-3"
      >
        <div class="mb-2 flex flex-wrap items-center gap-2 text-xs text-neutral-400">
          <el-tag size="small" type="warning">score {{ chunk.score.toFixed(4) }}</el-tag>
          <span v-if="chunk.documentTitle">文档：{{ chunk.documentTitle }}</span>
          <span v-if="chunk.collectionName">知识库：{{ chunk.collectionName }}</span>
          <span v-if="chunk.chunkIndex !== null && chunk.chunkIndex !== undefined">
            切片 #{{ chunk.chunkIndex }}
          </span>
        </div>
        <p class="whitespace-pre-wrap text-sm leading-6">{{ chunk.content }}</p>
      </el-card>
    </div>
    <el-empty v-else description="输入问题开始检索调试" />
  </div>
</template>
