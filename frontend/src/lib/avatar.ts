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
  options?: { maxSize?: number; quality?: number; mimeType?: string }
) {
  const maxSize = options?.maxSize ?? 512
  const quality = options?.quality ?? 0.86
  const mimeType = options?.mimeType ?? 'image/jpeg'

  const img = await createImageBitmap(file)
  const scale = Math.min(1, maxSize / Math.max(img.width, img.height))
  const w = Math.max(1, Math.round(img.width * scale))
  const h = Math.max(1, Math.round(img.height * scale))

  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h

  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('Canvas context not available')
  ctx.drawImage(img, 0, 0, w, h)

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

