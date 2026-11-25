import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// RAG 管理前端：端口 3001（3000 被主项目前端占用）
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3001,
    watch: {
      // Windows 上编辑器/格式化工具写配置时留下的临时目录会被 Vite 的 watcher 抓到，
      // 一旦文件被占用就 EBUSY 直接把 dev server 打挂，这里统一忽略掉。
      ignored: ['**/*.tmpdir/**', '**/.git/**', '**/dist/**'],
    },
    proxy: {
      // 同源代理：前端用相对路径 /rag-api 调 8002，浏览器不再发跨域预检。
      // 8002 的 CORS 白名单只放行 3001 两个来源，换个访问方式（本机别名、设计工作台、
      // 局域网 IP）就会被 400 掉，表现为前端一片 "Network Error"。
      '/rag-api': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/rag-api/, ''),
      },
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
