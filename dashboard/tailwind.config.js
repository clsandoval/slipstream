/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontSize: {
        giant: ['8rem', { lineHeight: '1' }],
        large: ['4rem', { lineHeight: '1.1' }],
        medium: ['2rem', { lineHeight: '1.25' }],
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
      },
      colors: {
        background: '#0f172a',
        surface: '#1e293b',
        muted: '#94a3b8',
        accent: '#38bdf8',
      },
    },
  },
  plugins: [],
};
