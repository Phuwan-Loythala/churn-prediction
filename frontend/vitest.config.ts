import { fileURLToPath } from 'node:url'
import { mergeConfig, defineConfig as defineVitestConfig, configDefaults } from 'vitest/config'
import viteConfig from './vite.config'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Vitest config merged with Vite config
export default mergeConfig(
  viteConfig,
  defineVitestConfig({
    test: {
      environment: 'jsdom',
      exclude: [...configDefaults.exclude, 'e2e/**'],
      root: fileURLToPath(new URL('./', import.meta.url)),
    },
  }),
)

// Vite config with Vue plugin
export const viteConfiguration = defineConfig({
  plugins: [vue()],
})
