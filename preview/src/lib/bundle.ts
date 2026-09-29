import { fileURLToPath } from 'node:url';
import { readPreviewBundle } from '../../../scripts/preview-bundle';
import { workspacePaths } from '../../../scripts/preview-workspace.mjs';
const root=fileURLToPath(new URL('../../../',import.meta.url));
const paths=workspacePaths(root,process.env.PARK_PREVIEW_WORKSPACE);
export const bundle=readPreviewBundle(paths.bundle);
