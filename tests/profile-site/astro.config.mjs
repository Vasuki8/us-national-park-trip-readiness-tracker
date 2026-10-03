import { defineConfig } from 'astro/config';
import { fileURLToPath } from 'node:url';
export default defineConfig({
  output: 'static', trailingSlash: 'always',
  outDir: fileURLToPath(new URL('../../.superpowers/profile-site/dist/', import.meta.url)),
  cacheDir: fileURLToPath(new URL('../../.superpowers/profile-site/cache/', import.meta.url)),
});
