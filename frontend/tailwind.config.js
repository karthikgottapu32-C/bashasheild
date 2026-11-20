/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          midnight: "#070B14",
          dark: "#0B1220",
          surface: "#0F182A",
          card: "#131F36",
          glass: "rgba(15, 24, 42, 0.75)"
        },
        cyan: {
          DEFAULT: "#00E5FF",
          glow: "rgba(0, 229, 255, 0.4)",
          subtle: "rgba(0, 229, 255, 0.12)"
        },
        neon: {
          blue: "#397BFF",
          glow: "rgba(57, 123, 255, 0.4)"
        },
        status: {
          emerald: "#00D68F",
          amber: "#FFB547",
          coral: "#FF4566"
        },
        txt: {
          primary: "#F5F7FA",
          secondary: "#8B9BB4",
          muted: "#5A6E8A"
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace']
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 18s linear infinite',
        'scan': 'scan 2.5s ease-in-out infinite'
      },
      keyframes: {
        scan: {
          '0%, 100%': { transform: 'translateY(-100%)' },
          '50%': { transform: 'translateY(100%)' }
        }
      }
    },
  },
  plugins: [],
}
