<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ChevronDown } from 'lucide-vue-next'

import { api, apiErrorMessage } from '@/lib/api'
import type { CollectionItem, CollectionPayload, CompanionItem, ParserConfig } from '@/lib/api'
import { useCollectionStore } from '@/stores/collections'

const props = defineProps<{
  modelValue: boolean
  /** 传入表示编辑，不传为新建 */
  collection?: CollectionItem | null
  companions: CompanionItem[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: [item: CollectionItem, isEdit: boolean]
}>()

const store = useCollectionStore()
const saving = ref(false)
const advanced = ref(false)
const formRef = ref()

const isEdit = computed(() => !!props.collection?.id)

const form = reactive({
  name: '',
  description: '',
  companionId: '',
  chunkSize: 500,
  chunkOverlap: 50,
  status: 'active',
  parser: {
    itemsPath: '',
    contentField: 'content',
    titleField: '',
    metaFields: '' as string,
  },
})

const rules = {
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度 1–100 个字符', trigger: 'blur' },
  ],
  // Milvus 用 companion_id 做 partition key，落库时为空会直接抛
  // 「Milvus 入库必须提供非空 companion_id」——后端建库不拦，但这类库永远存不进文档，
  // 所以在录入端就把它设成必填，别让用户建出一个只能看不能用的空壳库。
  companionId: [
    { required: true, message: '请选择绑定的角色：向量库按角色分区，未绑定的库无法入库', trigger: 'change' },
  ],
}

/** 预置伴侣不允许用户建库（后端 403），下拉里直接标注出来 */
const companionOptions = computed(() =>
  props.companions.map((c) => ({
    value: c.id,
    label: c.name,
    hint: c.id.startsWith('preset') ? '预置伴侣 · 不可建私有库' : '',
    disabled: c.id.startsWith('preset') && !isEdit.value,
  })),
)

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    advanced.value = false
    const c = props.collection
    form.name = c?.name || ''
    form.description = c?.description || ''
    form.companionId = c?.companionId || ''
    form.chunkSize = c?.chunkSize ?? 500
    form.chunkOverlap = c?.chunkOverlap ?? 50
    form.status = c?.status || 'active'
    const p = (c?.parserConfig || {}) as ParserConfig
    form.parser.itemsPath = p.itemsPath || ''
    form.parser.contentField = p.contentField || 'content'
    form.parser.titleField = p.titleField || ''
    form.parser.metaFields = (p.metaFields || []).join(', ')
    formRef.value?.clearValidate?.()
  },
)

function close() {
  emit('update:modelValue', false)
}

/** 只有填了内容字段才认为用户真的要自定义 JSON 规则 */
function buildParserConfig(): ParserConfig | null {
  const itemsPath = form.parser.itemsPath.trim()
  const titleField = form.parser.titleField.trim()
  const metaFields = form.parser.metaFields
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
  const contentField = form.parser.contentField.trim() || 'content'
  if (!itemsPath && !titleField && !metaFields.length && contentField === 'content') return null
  return { itemsPath: itemsPath || null, contentField, titleField: titleField || null, metaFields }
}

async function submit() {
  const ok = await formRef.value?.validate?.().catch(() => false)
  if (ok === false) return
  if (!form.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  if (!form.companionId) {
    ElMessage.warning('请先选择绑定的角色：库里没有角色分区就存不进向量库')
    return
  }
  if (form.chunkOverlap >= form.chunkSize) {
    ElMessage.warning('切片重叠必须小于切片长度，否则无法切分')
    return
  }

  const payload: CollectionPayload = {
    name: form.name.trim(),
    description: form.description.trim() || undefined,
    chunkSize: form.chunkSize,
    chunkOverlap: form.chunkOverlap,
    parserConfig: buildParserConfig(),
  }
  if (form.companionId) payload.companionId = form.companionId
  if (isEdit.value) payload.status = form.status

  saving.value = true
  try {
    const saved = isEdit.value
      ? await api.updateCollection(props.collection!.id, payload)
      : await api.createCollection(payload)
    store.invalidate()
    ElMessage.success(isEdit.value ? '已保存' : '知识库已创建')
    emit('saved', saved, isEdit.value)
    close()
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, '保存失败'))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <el-drawer
    :model-value="modelValue"
    :title="isEdit ? '编辑知识库' : '新建知识库'"
    size="520px"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
    >
      <el-form-item
        label="名称"
        prop="name"
      >
        <el-input
          v-model="form.name"
          maxlength="100"
          show-word-limit
          placeholder="例如：小智的项目知识库"
        />
      </el-form-item>

      <el-form-item label="描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="2"
          maxlength="200"
          placeholder="这个库里放什么内容，方便以后找"
        />
      </el-form-item>

      <el-form-item
        label="绑定角色"
        prop="companionId"
      >
        <el-select
          v-model="form.companionId"
          filterable
          placeholder="选择这个库归属的角色"
          class="w-full"
        >
          <el-option
            v-for="opt in companionOptions"
            :key="opt.value"
            :value="opt.value"
            :label="opt.label"
            :disabled="opt.disabled"
          >
            <span class="flex items-center justify-between">
              <span>{{ opt.label }}</span>
              <span
                v-if="opt.hint"
                class="ml-3 text-[12px] text-neutral-500"
              >{{ opt.hint }}</span>
            </span>
          </el-option>
        </el-select>
        <p class="mt-1 text-[12px] leading-4 text-neutral-600">
          必填。向量库按角色分区：绑定后该角色聊天时会自动检索这个库；未绑定的库无法入库文档。
          预置伴侣禁止挂私有库（后端拦截）。
        </p>
      </el-form-item>

      <el-form-item
        v-if="isEdit"
        label="状态"
      >
        <el-switch
          v-model="form.status"
          active-value="active"
          inactive-value="disabled"
          active-text="启用"
          inactive-text="停用"
        />
        <span class="ml-3 text-[12px] text-neutral-600">停用后检索不再命中该库，数据保留</span>
      </el-form-item>

      <!-- 高级参数 -->
      <button
        type="button"
        class="mb-3 flex w-full items-center gap-1.5 border-t border-ink-700/70 pt-4 text-[12px] text-neutral-500 hover:text-neutral-300"
        @click="advanced = !advanced"
      >
        <ChevronDown
          :size="13"
          :class="advanced ? 'rotate-0' : '-rotate-90'"
          class="transition-transform"
        />
        切片与解析参数
        <span class="ml-1 text-neutral-600">（默认 500 / 50，一般不用改）</span>
      </button>

      <div
        v-show="advanced"
        class="rounded-lg border border-ink-700/70 bg-ink-900/60 p-4"
      >
        <div class="grid grid-cols-2 gap-3">
          <el-form-item
            label="切片长度（字）"
            class="!mb-3"
          >
            <el-input-number
              v-model="form.chunkSize"
              :min="50"
              :max="2000"
              :step="50"
              controls-position="right"
              class="!w-full"
            />
          </el-form-item>
          <el-form-item
            label="重叠长度（字）"
            class="!mb-3"
          >
            <el-input-number
              v-model="form.chunkOverlap"
              :min="0"
              :max="500"
              :step="10"
              controls-position="right"
              class="!w-full"
            />
          </el-form-item>
        </div>
        <p class="-mt-1 mb-3 text-[12px] leading-4 text-neutral-600">
          整篇文档小于切片长度时会压成一块，多个话题混在一起会稀释语义（E-2 那类召回问题的根因）。
        </p>

        <p class="mb-2 text-[12px] text-neutral-400">
          JSON 解析规则（仅对 .json 文件生效）
        </p>
        <div class="grid grid-cols-2 gap-3">
          <el-form-item
            label="数组路径 itemsPath"
            class="!mb-3"
          >
            <el-input
              v-model="form.parser.itemsPath"
              placeholder="data.list"
            />
          </el-form-item>
          <el-form-item
            label="内容字段 contentField"
            class="!mb-3"
          >
            <el-input
              v-model="form.parser.contentField"
              placeholder="content"
            />
          </el-form-item>
          <el-form-item
            label="标题字段 titleField"
            class="!mb-3"
          >
            <el-input
              v-model="form.parser.titleField"
              placeholder="title（可空）"
            />
          </el-form-item>
          <el-form-item
            label="保留元数据 metaFields"
            class="!mb-3"
          >
            <el-input
              v-model="form.parser.metaFields"
              placeholder="author, url（逗号分隔）"
            />
          </el-form-item>
        </div>
        <p class="text-[12px] leading-4 text-neutral-600">
          不填则按默认规则（content 字段）。JSON 里有嵌套结构时必须配 itemsPath，否则整份文件会被当成一个对象切片。
        </p>
      </div>
    </el-form>

    <template #footer>
      <div class="flex justify-end gap-2">
        <el-button @click="close">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="saving"
          @click="submit"
        >
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>