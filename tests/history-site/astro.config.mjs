import { defineConfig } from 'astro/config';
import { fileURLToPath } from 'node:url';
export default defineConfig({
  output: 'static', trailingSlash: 'always',
  outDir: fileURLToPath(new URL('../../.superpowers/history-site/dist/', import.meta.url)),
  cacheDir: fileURLToPath(new URL('../../.superpowers/history-site/cache/', import.meta.url)),
});
