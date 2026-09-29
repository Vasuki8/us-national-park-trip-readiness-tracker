import { defineConfig } from 'astro/config';
export default defineConfig({
  output: 'static', trailingSlash: 'always',
  outDir: new URL('../../.superpowers/history-site/dist/', import.meta.url),
  cacheDir: new URL('../../.superpowers/history-site/cache/', import.meta.url),
});
