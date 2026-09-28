import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
test('server-side build code declares and enables Node types under TypeScript 6', () => {
  const pkg = JSON.parse(readFileSync('package.json', 'utf8'));
  const config = JSON.parse(readFileSync('tsconfig.json', 'utf8'));
  assert.match(pkg.devDependencies['@types/node'], /^\d+\.\d+\.\d+$/);
  assert.ok(config.compilerOptions.types.includes('node'));
});
