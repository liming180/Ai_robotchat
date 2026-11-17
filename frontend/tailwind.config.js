/** @type {import('tailwindcss').Config} */

/**
 * 色板说明：
 * - brand / mint / bone / ink 是项目实际视觉语言（暗色暖调），新代码一律用这四套。
 * - primary / accent / warm 是历史别名，值已换成新的暖调色，避免存量类名一次性改爆；
 *   新代码不要再引入。
 */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,vue}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      colors: {
        /* 主色：珊瑚橘 #ff8b72 */
        brand: {
          50: '#fff3ef',
          100: '#ffe3db',
          200: '#ffc9b9',
          300: '#ffb09b',
          400: '#ff9c81',
          500: '#ff8b72',
          600: '#f4735a',
          700: '#d95a42',
          800: '#b04530',
          900: '#8a3423',
        },
        /* 点缀：青绿 #65d8c5 */
        mint: {
          50: '#effcf9',
          100: '#d6f7f0',
          200: '#aeeee1',
          300: '#84e3d2',
          400: '#72dccb',
          500: '#65d8c5',
          600: '#4bbfa9',
          700: '#3a9a88',
          800: '#2d796c',
          900: '#245f55',
        },
        /* 反白块：米白 #e8e5dc */
        bone: {
          50: '#fbfaf7',
          100: '#f5f3ee',
          200: '#efede6',
          300: '#e8e5dc',
          400: '#dbd8d0',
          500: '#c9c5ba',
          600: '#aaa69a',
          700: '#85817a',
          800: '#5b5750',
          900: '#3a3733',
        },
        /* 暗底三层 */
        ink: {
          50: '#f6f4ef',
          100: '#e2e0d9',
          200: '#c2c1ba',
          300: '#aaa9a2',
          400: '#9a9c95',
          500: '#8d8f89',
          600: '#3a3e38',
          700: '#23271f',
          800: '#1e211e',
          900: '#1a1d1a',
          950: '#111311',
        },
        /* 知识/学习类第三色：暖黄 */
        amberish: {
          400: '#efc878',
          500: '#e8bd61',
          600: '#d0a44a',
        },

        /* ---- 历史别名（值已换新，勿在新代码使用） ---- */
        primary: {
          50: '#fff3ef',
          100: '#ffe3db',
          200: '#ffc9b9',
          300: '#ffb09b',
          400: '#ff9c81',
          500: '#ff8b72',
          600: '#f4735a',
          700: '#d95a42',
          800: '#b04530',
          900: '#8a3423',
        },
        accent: {
          50: '#effcf9',
          100: '#d6f7f0',
          200: '#aeeee1',
          300: '#84e3d2',
          400: '#72dccb',
          500: '#65d8c5',
          600: '#4bbfa9',
          700: '#3a9a88',
          800: '#2d796c',
          900: '#245f55',
        },
        warm: {
          50: '#fbfaf7',
          100: '#f5f3ee',
          200: '#efede6',
          300: '#e8e5dc',
          400: '#dbd8d0',
          500: '#c9c5ba',
          600: '#aaa69a',
          700: '#85817a',
          800: '#5b5750',
          900: '#3a3733',
        },
      },
      borderRadius: {
        card: '8px',
        btn: '7px',
        chip: '5px',
      },
      boxShadow: {
        card: '0 8px 24px rgba(0, 0, 0, 0.18)',
        lift: '0 12px 30px rgba(0, 0, 0, 0.28)',
        brand: '0 12px 30px rgba(255, 139, 114, 0.18)',
      },
      fontFamily: {
        sans: [
          'PingFang SC',
          'HarmonyOS Sans SC',
          'MiSans',
          'Microsoft YaHei',
          'system-ui',
          '-apple-system',
          'sans-serif',
        ],
        mono: ['SF Mono', 'JetBrains Mono', 'Consolas', 'ui-monospace', 'monospace'],
      },
      transitionTimingFunction: {
        out: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
};
