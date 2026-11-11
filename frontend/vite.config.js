import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const bypassHtmlNavigation = (req) => {
  if (req.method === 'GET' && req.headers.accept && req.headers.accept.includes('text/html')) {
    return '/index.html';
  }
};

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/static': { target: 'http://localhost:8000', changeOrigin: true },
      '/login': { target: 'http://localhost:8000', changeOrigin: true, bypass: bypassHtmlNavigation },
      '/logout': { target: 'http://localhost:8000', changeOrigin: true },
      '/cadastro': { target: 'http://localhost:8000', changeOrigin: true, bypass: bypassHtmlNavigation },
      '/adicionar-escopo': { target: 'http://localhost:8000', changeOrigin: true },
      '/australia': { target: 'http://localhost:8000', changeOrigin: true, bypass: bypassHtmlNavigation },
      '/botc': { target: 'http://localhost:8000', changeOrigin: true, bypass: bypassHtmlNavigation },
      '/caco': { target: 'http://localhost:8000', changeOrigin: true, bypass: bypassHtmlNavigation },
    },
  },
});