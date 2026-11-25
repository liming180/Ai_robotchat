/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // 与主应用一致的珊瑚色点缀
        accent: {
          DEFAULT: '#ef7d63',
          soft: '#f5a08c',
          dim: '#b85a45',
        },
        // 管理台深色底：950 页面 / 900 侧栏 / 850 卡片 / 800 悬浮 / 700 边框 / 600 分隔
        ink: {
          950: '#0a0c0f',
          900: '#0f1216',
          850: '#141821',
          800: '#1a1f29',
          700: '#232a36',
          600: '#2e3746',
        },
        // 深色底上重调的中性色：Tailwind 默认的 500/600 在 #0a0c0f 上只有 4.0/2.5 对比度，
        // 达不到 4.5:1。这一组按深色底反推，保证最暗的底（#232a36）上也 ≥4.5:1。
        neutral: {
          50: '#f4f7fa',
          100: '#e6ecf3',
          200: '#d2dae3',
          300: '#b4bfcc',
          400: '#a8b3c0',
          500: '#98a4b2',
          600: '#8b95a3',
          700: '#5f6b7a',
          800: '#39424f',
          900: '#222934',
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'PingFang SC',
          'Hiragino Sans GB',
          'Microsoft YaHei',
          'sans-serif',
        ],
      },
      boxShadow: {
        panel: '0 1px 0 0 rgba(255,255,255,0.03) inset, 0 8px 24px -16px rgba(0,0,0,0.9)',
      },
    },
  },
  plugins: [],
}