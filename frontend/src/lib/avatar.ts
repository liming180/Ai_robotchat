export type AvatarSvgOptions = {
  seed: string
  label: string
  size?: number
  radius?: number
}

function hashToHex(seed: string) {
  let h = 2166136261
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  const n = (h >>> 0).toString(16).padStart(8, '0')
  return n + n
}

export function createSvgAvatarDataUrl(options: AvatarSvgOptions) {
  const size = options.size ?? 256
  const radius = options.radius ?? Math.round(size / 4)
  const seed = options.seed || 'default'
  const label = (options.label || 'AI').trim().slice(0, 2)

  const hex = hashToHex(seed)
  const c1 = `#${hex.slice(0, 6)}`
  const c2 = `#${hex.slice(6, 12)}`
  const fontSize = Math.round(size * 0.34)

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="${c1}"/>
      <stop offset="1" stop-color="${c2}"/>
    </linearGradient>
  </defs>
  <rect width="${size}" height="${size}" rx="${radius}" fill="url(#g)"/>
  <text x="50%" y="54%" text-anchor="middle" dominant-baseline="middle"
        font-family="system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial"
        font-size="${fontSize}" fill="rgba(255,255,255,0.92)" font-weight="700">${label}</text>
</svg>`

  const encoded = btoa(unescape(encodeURIComponent(svg)))
  return `data:image/svg+xml;base64,${encoded}`
}

export async function compressImageFileToDataUrl(
  file: File,
  options?: { maxSize?: number; quality?: number; mimeType?: string; background?: string }
) {
  const img = await createImageBitmap(file)
  return drawToDataUrl(img, img.width, img.height, {
    maxSize: options?.maxSize,
    quality: options?.quality,
    mimeType: options?.mimeType,
    background: options?.background,
  })
}

/**
 * 把任意图片源光栅化为 JPEG data URL。
 *
 * <p>用途：SVG 无法直接上传（上传白名单只收位图，且 base64 体积远超 VARCHAR(500)），
 * 预设头像与降级头像在入库前必须先用它转成 JPEG。</p>
 */
export async function toJpegDataUrl(
  src: string,
  options?: { maxSize?: number; quality?: number; background?: string }
): Promise<string> {
  const img = await loadImage(src)
  return drawToDataUrl(img, img.naturalWidth, img.naturalHeight, {
    maxSize: options?.maxSize ?? 512,
    quality: options?.quality ?? 0.86,
    mimeType: 'image/jpeg',
    background: options?.background,
  })
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    // SVG data URL 需要显式声明跨域策略，否则 canvas 会被污染（toDataURL 抛 SecurityError）
    if (!src.startsWith('data:')) img.crossOrigin = 'anonymous'
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('图片加载失败'))
    img.src = src
  })
}

/**
 * 等比缩放到 maxSize 内绘制到 canvas 并导出 data URL。
 * 先铺底色再画图：JPEG 不支持透明，不垫底会把透明区域渲染成黑色。
 */
async function drawToDataUrl(
  source: CanvasImageSource,
  srcWidth: number,
  srcHeight: number,
  options: { maxSize?: number; quality?: number; mimeType?: string; background?: string }
): Promise<string> {
  const maxSize = options.maxSize ?? 512
  const quality = options.quality ?? 0.86
  const mimeType = options.mimeType ?? 'image/jpeg'
  const background = options.background ?? '#ffffff'

  const scale = Math.min(1, maxSize / Math.max(srcWidth, srcHeight))
  const w = Math.max(1, Math.round(srcWidth * scale))
  const h = Math.max(1, Math.round(srcHeight * scale))

  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h

  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('Canvas context not available')
  ctx.fillStyle = background
  ctx.fillRect(0, 0, w, h)
  ctx.drawImage(source, 0, 0, w, h)

  const blob: Blob = await new Promise((resolve, reject) => {
    canvas.toBlob(
      (b) => (b ? resolve(b) : reject(new Error('Image compression failed'))),
      mimeType,
      quality
    )
  })

  return await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(reader.error || new Error('Read file failed'))
    reader.readAsDataURL(blob)
  })
}

export function isQuotaExceededError(error: unknown) {
  if (!error) return false
  const anyErr = error as any
  return (
    anyErr?.name === 'QuotaExceededError' ||
    anyErr?.name === 'NS_ERROR_DOM_QUOTA_REACHED' ||
    String(anyErr?.message || '').toLowerCase().includes('quota')
  )
}

