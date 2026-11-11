import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/login': 'http://localhost:8000',
      '/logout': 'http://localhost:8000',
      '/cadastro': 'http://localhost:8000',
      '/adicionar-escopo': 'http://localhost:8000',
      '/api': 'http://localhost:8000',
      '/australia': 'http://localhost:8000',
      '/botc': 'http://localhost:8000',
      '/caco': 'http://localhost:8000',
    },
  },
});