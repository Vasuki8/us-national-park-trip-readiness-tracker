/** Prefix site-local absolute paths; external URLs and fragments stay unchanged. */
export function siteUrl(path: string, base: string): string {
  return path.startsWith('/') && !path.startsWith('//') ? base + path.slice(1) : path;
}
