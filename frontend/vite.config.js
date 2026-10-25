import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '127.0.0.1',
    proxy: {
      '/auth': 'http://127.0.0.1:8001',
      '/tickets': 'http://127.0.0.1:8001',
      '/agent': 'http://127.0.0.1:8001',
      '/threads': 'http://127.0.0.1:8001',
      '/health': 'http://127.0.0.1:8001'
    }
  }
})
