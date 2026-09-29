import { readPreviewBundle } from '../../../scripts/preview-bundle';
import { workspacePaths } from '../../../scripts/preview-workspace.mjs';
// The explicit build driver pins cwd to the repository root. import.meta.url is
// relocated into Astro's prerender chunks and must not locate source directories.
const paths=workspacePaths(process.cwd(),process.env.PARK_PREVIEW_WORKSPACE);
export const bundle=readPreviewBundle(paths.bundle);
