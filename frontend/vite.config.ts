import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/analyze': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/stats': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/scans': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/evaluation': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
