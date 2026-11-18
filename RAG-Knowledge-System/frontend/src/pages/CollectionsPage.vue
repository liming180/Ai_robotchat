<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { api } from '@/lib/api'
import type { CollectionItem, CompanionItem } from '@/lib/api'

const router = useRouter()
const loading = ref(false)
const items = ref<CollectionItem[]>([])
const total = ref(0)
const companions = ref<CompanionItem[]>([])
const query = reactive({ keyword: '', companionId: '', page: 1, pageSize: 10 })

const dialogVisible = ref(false)
const editing = ref<CollectionItem | null>(null)
const form = reactive({ name: '', description: '', companionId: '' })

async function load() {
  loading.value = true
  try {
    const data = await api.listCollections({
      keyword: query.keyword.trim() || undefined,
      companionId: query.companionId || undefined,
      page: query.page,
      pageSize: query.pageSize,
    })
    items.value = data.items
    total.value = data.total
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.name = ''
  form.description = ''
  form.companionId = ''
  dialogVisible.value = true
}

function openEdit(row: CollectionItem) {
  editing.value = row
  form.name = row.name
  form.description = row.description || ''
  form.companionId = row.companionId || ''
  dialogVisible.value = true
}

async function save() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  const payload = {
    name: form.name.trim(),
    description: form.description.trim() || undefined,
    companionId: form.companionId || undefined,
  }
  try {
    if (editing.value) {
      await api.updateCollection(editing.value.id, payload)
    } else {
      await api.createCollection(payload)
    }
    ElMessage.success('已保存')
    dialogVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '保存失败')
  }
}

async function remove(row: CollectionItem) {
  try {
    await ElMessageBox.confirm(
      `确定删除知识库「${row.name}」？其文档、切片与向量会一并删除`,
      '删除确认',
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await api.deleteCollection(row.id)
    ElMessage.success('已删除')
    await load()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '删除失败')
  }
}

onMounted(async () => {
  await load()
  try {
    companions.value = (await api.listCompanions()).items
  } catch {
    // 主库不可用时角色下拉留空，不影响列表
  }
})
</script>

<template>
  <div>
    <div class="mb-4 flex items-center gap-3">
      <el-input
        v-model="query.keyword"
        placeholder="搜索名称"
        clearable
        class="!w-56"
        @keyup.enter="query.page = 1; load()"
        @clear="query.page = 1; load()"
      />
      <el-select
        v-model="query.companionId"
        placeholder="全部角色"
        clearable
        class="!w-44"
        @change="query.page = 1; load()"
      >
        <el-option v-for="c in companions" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-button @click="query.page = 1; load()">查询</el-button>
      <el-button type="primary" class="ml-auto" @click="openCreate">新建知识库</el-button>
    </div>

    <el-table v-loading="loading" :data="items">
      <el-table-column prop="name" label="名称" min-width="160" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column label="文档 / 切片" width="110">
        <template #default="{ row }">{{ row.documentCount }} / {{ row.chunkCount }}</template>
      </el-table-column>
      <el-table-column label="向量配置" width="190">
        <template #default="{ row }">
          {{ row.embeddingModel }} · {{ row.embeddingDim }} 维 · {{ row.embeddingBackend }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="90" />
      <el-table-column label="操作" width="190" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="router.push(`/collections/${row.id}`)">
            详情
          </el-button>
          <el-button link @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="mt-4 justify-end"
      layout="total, prev, pager, next"
      :total="total"
      v-model:current-page="query.page"
      :page-size="query.pageSize"
      @current-change="load"
    />

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑知识库' : '新建知识库'" width="480">
      <el-form label-position="top">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="绑定角色（可选）">
          <el-select v-model="form.companionId" placeholder="不绑定" clearable class="w-full">
            <el-option v-for="c in companions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
