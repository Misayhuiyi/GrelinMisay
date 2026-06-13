import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@tarojs/components': path.resolve(__dirname, 'src/taro-adapter/components'),
      '@tarojs/taro': path.resolve(__dirname, 'src/taro-adapter/taro'),
    },
  },
  server: {
    port: 10086,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});