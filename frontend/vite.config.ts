import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],

  // Dev proxy: forward API calls to the FastAPI backend to avoid CORS in development.
  server: {
    proxy: {
      '/upload-chart': 'http://localhost:8000',
      '/check-safety': 'http://localhost:8000',
      '/sessions': 'http://localhost:8000',
      '/voice-session': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
