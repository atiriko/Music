import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  plugins: [react(), {
    name: 'development-csp',
    transformIndexHtml(html, context) {
      return context.server ? html.replace("'wasm-unsafe-eval';", "'wasm-unsafe-eval' 'unsafe-inline';").replace("connect-src 'self';", "connect-src 'self' ws://127.0.0.1:*;") : html;
    },
  }],
  base: './',
  build: { target: 'es2022', sourcemap: true },
  worker: { format: 'es' },
  server: { host: '127.0.0.1', port: 5173, strictPort: true },
});
