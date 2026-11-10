import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// En desarrollo, las peticiones `/api` se redirigen al backend en :8000.
// En producción (Docker + Nginx) el proxy lo resuelve `nginx.conf`.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: process.env.VITE_DEV_API_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
});
