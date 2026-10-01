import { readPreviewBundle } from '../../../scripts/preview-bundle';
import { workspacePaths } from '../../../scripts/preview-workspace.mjs';
// The driver pins the source root separately and runs Astro inside its private
// workspace. import.meta.url moves into prerender chunks during the build.
const paths=workspacePaths(process.env.PARK_PREVIEW_PROJECT_ROOT,process.env.PARK_PREVIEW_WORKSPACE);
export const bundle=readPreviewBundle(paths.bundle);
