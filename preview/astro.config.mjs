import { defineConfig } from 'astro/config';
import { fileURLToPath } from 'node:url';
import { workspacePaths, readReady } from '../scripts/preview-workspace.mjs';
const root=fileURLToPath(new URL('../',import.meta.url));
const workspace=process.env.PARK_PREVIEW_WORKSPACE;
const paths=workspacePaths(root,workspace);
if(process.argv.includes('dev'))throw new Error('Use the explicit private preview build; development-server fallback is disabled.');
if(process.argv.includes('preview'))readReady(root,workspace);
export default defineConfig({
  output:'static',trailingSlash:'always',outDir:paths.output,cacheDir:paths.cache,
  // Prerender chunks live outside the checkout's node_modules ancestry.
  vite:{environments:{prerender:{resolve:{noExternal:true}}}},
  server:{host:'127.0.0.1',port:4323},
});
