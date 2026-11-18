<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadUserFile } from 'element-plus'

import { api } from '@/lib/api'
import type { CollectionItem, DocumentItem } from '@/lib/api'

const route = useRoute()
const collectionId = route.params.id as string

const collection = ref<CollectionItem | null>(null)
const loading = ref(false)
const docs = ref<DocumentItem[]>([])
const fileList = ref<UploadUserFile[]>([])
const uploading = ref(false)

const manualVisible = ref(false)
const manual = reactive({ title: '', content: '' })

// 任务终态（后端 status 取值含 completed / failed 等，progress>=100 视为兜底终态）
const TERMINAL_STATUS = ['completed', 'failed', 'success', 'error', 'done']
let timer: number | undefined

async function load() {
  loading.value = true
  try {
    collection.value = await api.getCollection(collectionId)
    const data = await api.listDocuments(collectionId)
    docs.value = data?.items ?? []
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载失败')
  } finally {
    loading.value = false
  }
}

/** 轮询任务进度，全部到终态后刷新列表 */
function pollTasks(taskIds: string[]) {
  if (!taskIds.length) return
  window.clearInterval(timer)
  timer = window.setInterval(async () => {
    try {
      const states = await Promise.all(taskIds.map((id) => api.getTask(id)))
      const allDone = states.every(
        (s) => TERMINAL_STATUS.includes(s.status) || s.progress >= 100,
      )
      if (allDone) {
        window.clearInterval(timer)
        const failed = states.find((s) => s.status === 'failed' || s.status === 'error')
        if (failed) {
          ElMessage.error(`处理失败：${failed.errorMsg || '未知错误'}`)
        } else {
          ElMessage.success('全部处理完成')
        }
        await load()
      }
    } catch {
      window.clearInterval(timer)
    }
  }, 2000)
}

async function doUpload() {
  const files = fileList.value
    .map((f) => f.raw)
    .filter((f): f is NonNullable<typeof f> => !!f)
  if (!files.length) {
    ElMessage.warning('请先选择 json / md / txt 文件')
    return
  }
  uploading.value = true
  try {
    const result: any = await api.uploadDocuments(collectionId, files)
    const items = Array.isArray(result) ? result : [result]
    const taskIds = items.map((i: any) => i?.taskId).filter(Boolean) as string[]
    ElMessage.success(`已提交 ${taskIds.length} 个文件的解析任务`)
    fileList.value = []
    pollTasks(taskIds)
    await load()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '上传失败')
  } finally {
    uploading.value = false
  }
}

async function saveManual() {
  if (!manual.title.trim() || !manual.content.trim()) {
    ElMessage.warning('标题和内容不能为空')
    return
  }
  try {
    const res: any = await api.createManualDocument(collectionId, {
      title: manual.title.trim(),
      content: manual.content.trim(),
    })
    manualVisible.value = false
    manual.title = ''
    manual.content = ''
    ElMessage.success('已提交入库任务')
    if (res?.taskId) pollTasks([res.taskId])
    await load()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '提交失败')
  }
}

async function reindex(row: DocumentItem) {
  try {
    const res: any = await api.reindexDocument(row.id)
    ElMessage.success('已重新解析入库')
    if (res?.taskId) pollTasks([res.taskId])
    await load()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '操作失败')
  }
}

async function removeDoc(row: DocumentItem) {
  try {
    await ElMessageBox.confirm(`确定删除文档「${row.title}」？其切片与向量会一并删除`, '删除确认', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await api.deleteDocument(row.id)
    ElMessage.success('已删除')
    await load()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '删除失败')
  }
}

function statusTagType(status?: string): 'success' | 'danger' | 'warning' | 'info' {
  if (status === 'completed' || status === 'active') return 'success'
  if (status === 'failed' || status === 'error') return 'danger'
  if (status === 'processing' || status === 'parsing' || status === 'indexing') return 'warning'
  return 'info'
}

onMounted(load)
onUnmounted(() => window.clearInterval(timer))
</script>

<template>
  <div>
    <div class="mb-4 flex items-center gap-3">
      <el-page-header @back="$router.back()">
        <template #content>
          <span class="text-base font-medium">{{ collection?.name || '知识库详情' }}</span>
        </template>
      </el-page-header>
      <span v-if="collection" class="text-sm text-neutral-400">
        {{ collection.embeddingModel }} · {{ collection.embeddingDim }} 维 ·
        {{ collection.embeddingBackend }} · 切片 {{ collection.chunkSize }}/{{ collection.chunkOverlap }}
      </span>
    </div>

    <el-card shadow="never" class="mb-4">
      <div class="flex flex-wrap items-center gap-4">
        <el-upload
          v-model:file-list="fileList"
          class="flex-1 min-w-[280px]"
          drag
          multiple
          :auto-upload="false"
          accept=".json,.md,.txt"
        >
          <div class="py-2 text-sm text-neutral-400">
            拖拽或点击选择文件（json / md / txt，单个 ≤ 20MB），选好后点「上传并解析」
          </div>
        </el-upload>
        <div class="flex flex-col gap-2">
          <el-button type="primary" :loading="uploading" @click="doUpload">上传并解析</el-button>
          <el-button @click="manualVisible = true">手动写知识</el-button>
        </div>
      </div>
    </el-card>

    <el-table v-loading="loading" :data="docs">
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="sourceType" label="来源" width="100" />
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="进度" width="80">
        <template #default="{ row }">{{ row.progress }}%</template>
      </el-table-column>
      <el-table-column prop="chunkCount" label="切片数" width="90" />
      <el-table-column prop="errorMsg" label="错误信息" min-width="140" show-overflow-tooltip />
      <el-table-column prop="updatedAt" label="更新时间" width="170" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="reindex(row)">重索引</el-button>
          <el-button link type="danger" @click="removeDoc(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="manualVisible" title="手动写知识" width="560">
      <el-form label-position="top">
        <el-form-item label="标题" required>
          <el-input v-model="manual.title" maxlength="255" show-word-limit />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="manual.content" type="textarea" :rows="8" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="manualVisible = false">取消</el-button>
        <el-button type="primary" @click="saveManual">提交入库</el-button>
      </template>
    </el-dialog>
  </div>
</template>
