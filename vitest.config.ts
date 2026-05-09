import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['src/**/*.{test,spec}.{ts,tsx}', 'tests/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['tests/structural/**', 'node_modules/**', 'dist/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
  resolve: {
    alias: {
      '@/types': new URL('./src/types', import.meta.url).pathname,
      '@/config': new URL('./src/config', import.meta.url).pathname,
      '@/repo': new URL('./src/repo', import.meta.url).pathname,
      '@/service': new URL('./src/service', import.meta.url).pathname,
      '@/runtime': new URL('./src/runtime', import.meta.url).pathname,
      '@/ui': new URL('./src/ui', import.meta.url).pathname,
    },
  },
});
