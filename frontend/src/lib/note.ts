/**
 * 笔记标题派生。
 *
 * 后端不存 title 列：标题是展示层的派生物。
 * 先对整段内容做 trim（开头的空行不算数），再按首行判断：
 *
 * 1. 首行长度 ≤ TITLE_MAX_LEN  → 首行作标题，其余行作正文；
 * 2. 首行超长（> 60 字）        → 说明它不是标题而是一整段话，
 *                                 整体作正文，不渲染标题；
 * 3. 只有一行                   → 标题即全文，正文为空
 *                                 （卡片只显示一行标题，设计稿的边界情况）。
 *
 * 这样既不会为了凑标题把一段话截断成「半句话标题 + 半句话正文」，也不会丢字。
 */

/** 首行超过这个长度就不当标题用 */
export const TITLE_MAX_LEN = 60

export interface NoteContentParts {
  /** 空串表示没有标题，调用方应省略 h3 */
  title: string
  /** 空串表示没有正文，调用方应省略正文区块 */
  body: string
}

export const splitNoteContent = (content: string): NoteContentParts => {
  const text = content.replace(/\r\n/g, '\n').trim()
  if (!text) return { title: '', body: '' }

  const newlineAt = text.indexOf('\n')
  // 无换行：整条是一行
  if (newlineAt === -1) {
    return text.length <= TITLE_MAX_LEN
      ? { title: text, body: '' }
      : { title: '', body: text }
  }

  const firstLine = text.slice(0, newlineAt).trim()
  const rest = text.slice(newlineAt + 1).trim()

  if (firstLine.length > TITLE_MAX_LEN) {
    // 首行过长：说明首行就是一整段话，整体作正文，不派生标题
    return { title: '', body: text }
  }
  // 防御分支：text 已 trim，首行理论不会是空串；真出现就整体当正文，不派生出空标题
  if (!firstLine) return { title: '', body: text }

  return { title: firstLine, body: rest }
}
