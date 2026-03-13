/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'tech': {
          'bg': {
            'primary': '#0a0e1a',
            'secondary': '#111827',
            'tertiary': '#1a1f2e',
            'card': 'rgba(17, 24, 39, 0.6)',
          },
          'neon': {
            'blue': '#00d4ff',
            'purple': '#a855f7',
            'pink': '#ec4899',
            'green': '#10b981',
            'yellow': '#fbbf24',
          },
          'text': {
            'primary': '#f3f4f6',
            'secondary': '#9ca3af',
            'muted': '#6b7280',
          }
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'tech-mesh': 'linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%)',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s infinite',
        'gradient-shift': 'gradient-shift 8s ease infinite',
        'scan-line': 'scan-line 8s linear infinite',
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}