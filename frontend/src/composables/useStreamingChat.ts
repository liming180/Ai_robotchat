import { ref } from 'vue'
import { getAiBase } from '@/lib/api'

export function useStreamingChat() {
  const streamingContent = ref('')
  const isStreaming = ref(false)

  async function sendStreaming(
    userMessage: string,
    systemPrompt: string,
    historyMessages: Array<{ role: string; content: string; images?: string[] }>,
    onChunk?: (text: string) => void,
    images?: string[],
    enableRAG: boolean = true,
    /** Java 登录用户的 UUID，Python 记忆/情绪按它路由（P0-3） */
    userId?: string | null
  ): Promise<string> {
    isStreaming.value = true
    streamingContent.value = ''

    try {
      // 根据是否启用RAG选择不同的API端点
      const endpoint = enableRAG ? '/api/v1/ai/chat/langchain/stream' : '/api/v1/ai/chat/stream'
      const res = await fetch(`${getAiBase()}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userMessage,
          systemPrompt,
          messages: historyMessages,
          images: images?.length ? images : undefined,
          // 未登录时传 undefined，由 Python 端使用匿名标识；守卫已保证正常路径下必有值
          userId: userId ?? undefined,
        }),
      })

      if (!res.ok || !res.body) {
        throw new Error(`AI 服务响应异常 (HTTP ${res.status})`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''
      let full = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buf += decoder.decode(value, { stream: true })
        const lines = buf.split('\n')
        buf = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const payload = JSON.parse(line.slice(6))
            if (payload.delta) {
              full += payload.delta
              streamingContent.value = full
              onChunk?.(full)
            }
          } catch (e) {
            throw new Error('AI 流式响应解析失败')
          }
        }
      }

      if (!full.trim()) {
        throw new Error('AI 未生成有效内容')
      }

      return full
    } catch (error) {
      isStreaming.value = false
      throw error // 重新抛出错误，让调用者处理
    }
  }

  async function fetchSuggestions(
    systemPrompt: string,
    historyMessages: Array<{ role: string; content: string }>,
  ): Promise<string[]> {
    try {
      const res = await fetch(`${getAiBase()}/api/v1/ai/suggestions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ systemPrompt, messages: historyMessages }),
      })
      if (!res.ok) {
        throw new Error(`建议服务响应异常 (HTTP ${res.status})`)
      }
      const data = await res.json()
      if (!data?.data?.suggestions) {
        throw new Error('AI 未返回有效的建议数据')
      }
      return data.data.suggestions
    } catch (error) {
      throw error // 重新抛出错误，让调用者处理
    }
  }

  function reset() {
    streamingContent.value = ''
    isStreaming.value = false
  }

  return { streamingContent, isStreaming, sendStreaming, fetchSuggestions, reset }
}
