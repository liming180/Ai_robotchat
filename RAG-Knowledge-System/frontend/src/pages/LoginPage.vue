<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowRight, Boxes, KeyRound, Mail } from 'lucide-vue-next'

import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const form = reactive({ email: '', password: '' })

async function submit() {
  if (!form.email.trim() || !form.password) {
    ElMessage.warning('请输入邮箱和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(form.email.trim(), form.password)
    ElMessage.success('登录成功')
    // 保留来源页，被 401 踢出时能回到原位置
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/overview'
    router.push(redirect)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="grid h-full place-items-center bg-ink-950 px-6">
    <div class="w-full max-w-[860px] overflow-hidden rounded-2xl border border-ink-700 bg-ink-900 shadow-panel">
      <div class="grid md:grid-cols-[1fr_1.05fr]">
        <!-- 左侧品牌说明 -->
        <div class="hidden flex-col justify-between border-r border-ink-700/70 bg-ink-850 p-8 md:flex">
          <div class="flex items-center gap-2.5">
            <span class="grid size-8 place-items-center rounded-lg bg-accent/15 text-accent ring-1 ring-accent/30">
              <Boxes :size="17" />
            </span>
            <span class="text-[13px] font-semibold text-neutral-100">RAG 知识库</span>
          </div>
          <div>
            <p class="text-[15px] font-medium leading-6 text-neutral-200">
              为每个 AI 伴侣<br>挂载专属知识
            </p>
            <p class="mt-3 text-[13px] leading-6 text-neutral-500">
              上传文档、拆分切片、向量化入库，聊天时按角色路由检索。 知识库控制台与管理后台共用同一套账号。
            </p>
          </div>
          <p class="mono text-neutral-600">
            Milvus 2.6 · embedding-3 · 2048d
          </p>
        </div>

        <!-- 右侧登录表单 -->
        <div class="p-8">
          <h1 class="text-[17px] font-semibold text-neutral-50">
            登录控制台
          </h1>
          <p class="mt-1 text-[13px] text-neutral-500">
            使用主应用账号，无需单独注册
          </p>

          <el-form
            class="mt-6"
            label-position="top"
            @submit.prevent="submit"
          >
            <el-form-item label="邮箱">
              <el-input
                v-model="form.email"
                size="large"
                placeholder="you@example.com"
                :prefix-icon="Mail"
                @keyup.enter="submit"
              />
            </el-form-item>
            <el-form-item label="密码">
              <el-input
                v-model="form.password"
                size="large"
                type="password"
                show-password
                placeholder="主应用登录密码"
                :prefix-icon="KeyRound"
                @keyup.enter="submit"
              />
            </el-form-item>
            <el-button
              class="mt-2 w-full"
              type="primary"
              size="large"
              :loading="loading"
              @click="submit"
            >
              登录
              <ArrowRight
                :size="15"
                class="ml-1"
              />
            </el-button>
          </el-form>

          <p class="mt-5 text-[12px] leading-5 text-neutral-600">
            登录凭证由 Java 业务后端签发，RAG 服务只验签不落库。
          </p>
        </div>
      </div>
    </div>
  </div>
</template>