/**
 * 图片工具
 *
 * 从 ChatPage.vue 抽出来的压缩逻辑：聊天发图和个人空间换头像都要用，
 * 原来只写在聊天页里，个人空间要用就得复制一份，所以收到这里共用。
 */

/** 压缩目标长边上限（px） */
const DEFAULT_MAX = 1024
/** JPEG 质量 */
const DEFAULT_QUALITY = 0.85

/**
 * 把 File / Blob 压成 base64 JPEG data URL。
 *
 * 为什么压缩：原图动辄几 MB，直接 base64 塞进请求体会让消息体和头像更新请求巨大，
 * 而且聊天链路还要把 base64 转给 Python 视觉模型，过大容易超时。
 *
 * @param file 源文件
 * @param max 长边上限，超过则等比缩小
 * @param quality JPEG 质量 0–1
 */
export function compressImage(
  file: File | Blob,
  max = DEFAULT_MAX,
  quality = DEFAULT_QUALITY,
): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = (e) => {
      const img = new Image()

      img.onload = () => {
        let { width, height } = img

        if (width > max || height > max) {
          if (width > height) {
            height = Math.round((height * max) / width)
            width = max
          } else {
            width = Math.round((width * max) / height)
            height = max
          }
        }

        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height

        const ctx = canvas.getContext('2d')
        if (!ctx) {
          reject(new Error('浏览器不支持 canvas，无法处理图片'))
          return
        }

        ctx.drawImage(img, 0, 0, width, height)
        resolve(canvas.toDataURL('image/jpeg', quality))
      }

      img.onerror = () => reject(new Error('图片解码失败，请换一张试试'))
      img.src = e.target?.result as string
    }

    reader.onerror = () => reject(new Error('读取文件失败'))
    reader.readAsDataURL(file)
  })
}

/** 判断 data URL 的原始大小（KB），用于上传前提示 */
export function dataUrlSizeKb(dataUrl: string): number {
  // data:image/jpeg;base64,XXXX → 只算 base64 部分
  const base64 = dataUrl.split(',')[1] ?? ''
  return Math.round((base64.length * 3) / 4 / 1024)
}
