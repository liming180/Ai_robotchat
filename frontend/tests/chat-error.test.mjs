/**
 * 回归用例：frontend/src/lib/chatError.ts（P2-5 动作 2）
 *
 * Node 24 原生类型擦除可直接 import .ts，无需额外测试框架。
 * 执行：node tests/chat-error.test.mjs（或 npm run test:error）
 */

import assert from 'node:assert/strict'
import { describeChatError, extractHttpStatus } from '../src/lib/chatError.ts'

let passed = 0
let failed = 0

function check(name, fn) {
  try {
    fn()
    passed++
    console.log(`  PASS  ${name}`)
  } catch (error) {
    failed++
    console.log(`  FAIL  ${name}`)
    console.log(`        ${error.message}`)
  }
}

function expectMessage(name, error, expected) {
  check(name, () => assert.equal(describeChatError(error), expected))
}

console.log('用例组 1：HTTP 状态码分支')
expectMessage(
  '401 → 鉴权失败，点名 token',
  new Error('AI 服务响应异常 (HTTP 401)'),
  'AI 服务鉴权失败（401）：服务间 token 不一致，请重启前端/后端或核对 SERVICE_TOKEN。',
)
check('401 文案包含 401 与 token', () => {
  const text = describeChatError(new Error('AI 服务响应异常 (HTTP 401)'))
  assert.ok(text.includes('401'))
  assert.ok(text.includes('token'))
})
expectMessage(
  '403 → 拒绝访问',
  new Error('AI 服务响应异常 (HTTP 403)'),
  'AI 服务拒绝访问（403），请确认服务间权限配置。',
)
expectMessage(
  '404 → 接口不存在',
  new Error('AI 服务响应异常 (HTTP 404)'),
  'AI 服务接口不存在（404），请确认服务版本与端口。',
)
expectMessage(
  '429 → 频控提示',
  new Error('AI 服务响应异常 (HTTP 429)'),
  '请求过于频繁（429），请稍等片刻再重试。',
)
expectMessage(
  '500 → 内部错误带真实状态码',
  new Error('AI 服务响应异常 (HTTP 500)'),
  'AI 服务内部错误（HTTP 500），请稍后重试。',
)
expectMessage(
  '502 → 内部错误带真实状态码',
  new Error('AI 服务响应异常 (HTTP 502)'),
  'AI 服务内部错误（HTTP 502），请稍后重试。',
)
expectMessage(
  '其他 4xx → 通用状态码文案',
  new Error('AI 服务响应异常 (HTTP 400)'),
  'AI 服务响应异常（HTTP 400），请重试。',
)
expectMessage(
  '200 但无响应体 → 通用状态码文案',
  new Error('AI 服务响应异常 (HTTP 200)'),
  'AI 服务响应异常（HTTP 200），请重试。',
)

console.log('用例组 2：网络层错误（fetch TypeError 三种措辞）')
const networkText = '连不上 AI 服务，请确认后端服务已启动。'
expectMessage('Failed to fetch', new TypeError('Failed to fetch'), networkText)
expectMessage('Load failed（Safari）', new TypeError('Load failed'), networkText)
expectMessage(
  'NetworkError when attempting to fetch resource.',
  new TypeError('NetworkError when attempting to fetch resource.'),
  networkText,
)
expectMessage(
  '非 TypeError 但信息形如网络错误',
  new Error('fetch failed'),
  networkText,
)

console.log('用例组 3：解析失败 / 空内容（文案与改造前一致）')
expectMessage(
  '流式响应解析失败',
  new Error('AI 流式响应解析失败'),
  'AI 响应解析失败，请重试。',
)
expectMessage(
  'AI 未生成有效内容',
  new Error('AI 未生成有效内容'),
  'AI 未生成有效内容，请尝试重新发送消息。',
)
expectMessage(
  '建议数据缺失',
  new Error('AI 未返回有效的建议数据'),
  'AI 建议数据异常，请重试。',
)

console.log('用例组 4：建议服务复用状态码映射')
expectMessage(
  '建议服务 401',
  new Error('建议服务响应异常 (HTTP 401)'),
  '建议服务鉴权失败（401）：服务间 token 不一致，请重启前端/后端或核对 SERVICE_TOKEN。',
)
expectMessage(
  '建议服务 503',
  new Error('建议服务响应异常 (HTTP 503)'),
  '建议服务内部错误（HTTP 503），请稍后重试。',
)

console.log('用例组 5：兜底')
expectMessage('非 Error 值', 'boom', 'AI 服务暂时不可用，请稍后再试。')
expectMessage('无法归类的 Error', new Error('something else'), 'AI 服务暂时不可用，请稍后再试。')

console.log('用例组 6：extractHttpStatus')
check('提取 401', () => assert.equal(extractHttpStatus('AI 服务响应异常 (HTTP 401)'), 401))
check('小写 http 也能提取', () => assert.equal(extractHttpStatus('failed http 502'), 502))
check('无状态码返回 undefined', () => assert.equal(extractHttpStatus('AI 流式响应解析失败'), undefined))

console.log(`\n结果：${passed} 通过，${failed} 失败`)
if (failed > 0) process.exit(1)
