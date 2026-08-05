import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    // Genera el build compilado directo en una carpeta de estáticos de Django
    outDir: path.resolve(__dirname, '../static/frontend'),
    emptyOutDir: true,
  },
  server: {
    // Configura proxy para cuando desarrolles con 'npm run dev'
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true
      }
    }
  }
})