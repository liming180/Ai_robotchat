<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { api, apiErrorMessage } from '@/lib/api'
import type { DocumentItem } from '@/lib/api'

const props = defineProps<{
  modelValue: boolean
  /** 新建目标知识库 */
  collectionId: string
  /** 传入则为编辑已有 manual 文档（只需 id 与标题，正文由抽屉自己拉） */
  document?: DocumentItem | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: [taskId: string]
}>()

const saving = ref(false)
const formRef = ref()
const isEdit = computed(() => !!props.document?.id)

const form = reactive({ title: '', content: '' })
const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入正文内容', trigger: 'blur' }],
}

watch(
  () => props.modelValue,
  async (open) => {
    if (!open) return
    form.title = props.document?.title || ''
    form.content = ''
    formRef.value?.clearValidate?.()
    if (isEdit.value && props.document?.id) {
      // 列表数据不带正文，编辑前先拉一次详情
      try {
        const detail = await api.getDocument(props.document.id, true)
        form.content = detail.rawContent || ''
      } catch (e) {
        ElMessage.error(apiErrorMessage(e, '原文读取失败'))
        emit('update:modelValue', false)
      }
    }
  },
)

async function submit() {
  const ok = await formRef.value?.validate?.().catch(() => false)
  if (ok === false) return

  saving.value = true
  try {
    if (isEdit.value && props.document) {
      const res = await api.updateDocument(props.document.id, {
        title: form.title.trim(),
        content: form.content,
      })
      ElMessage.success('已保存，正在重新切片入库')
      emit('saved', res.taskId)
    } else {
      const res = await api.createManualDocument(props.collectionId, {
        title: form.title.trim(),
        content: form.content,
      })
      ElMessage.success('已录入，正在后台解析')
      emit('saved', res.taskId)
    }
    emit('update:modelValue', false)
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
    :title="isEdit ? '编辑手动文档' : '录入知识'"
    size="560px"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
    >
      <el-form-item
        label="标题"
        prop="title"
      >
        <el-input
          v-model="form.title"
          maxlength="200"
          placeholder="例如：接口鉴权约定"
        />
      </el-form-item>
      <el-form-item
        label="正文"
        prop="content"
      >
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="16"
          maxlength="50000"
          show-word-limit
          placeholder="支持 Markdown。列表条目会按行拆成独立切片，更容易被检索命中。"
        />
      </el-form-item>
      <p class="text-[12px] leading-4 text-neutral-600">
        保存后新建解析任务，旧的切片与向量会被替换；仅手动录入的文档可编辑，上传文件如需更正请重新上传。
      </p>
    </el-form>

    <template #footer>
      <div class="flex justify-end gap-2">
        <el-button @click="emit('update:modelValue', false)">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="saving"
          @click="submit"
        >
          {{ isEdit ? '保存' : '录入' }}
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>