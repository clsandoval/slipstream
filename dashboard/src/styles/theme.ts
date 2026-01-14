export const theme = {
  colors: {
    background: '#0f172a',  // slate-900
    surface: '#1e293b',     // slate-800
    text: '#f8fafc',        // slate-50
    muted: '#94a3b8',       // slate-400
    accent: '#38bdf8',      // sky-400
    success: '#22c55e',     // green-500
    warning: '#f59e0b',     // amber-500
  },
  fontSize: {
    giant: '8rem',   // 128px - stroke rate
    large: '4rem',   // 64px - timer, labels
    medium: '2rem',  // 32px - secondary info
    small: '1.25rem', // 20px - captions
  },
  fontFamily: {
    sans: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, sans-serif',
    mono: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
  },
} as const;
