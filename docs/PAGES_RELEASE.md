# Gated GitHub Pages release and rollback

## Purpose

`.github/workflows/pages-release.yml` provides a manual production-hosting mechanism without automatically publishing the pilot.

Creating the workflow does **not** make the website live. It has only a `workflow_dispatch` trigger.

## Release inputs

A dispatch requires:

- `mode`: `deploy` or `rollback`;
- `target_sha`: exact lowercase 40-character commit SHA;
- `verify_run_id`: GitHub Actions run ID for a successful `Verify pilot` run;
- `confirmation`:
  - `DEPLOY_VERIFIED_PILOT` for deploy;
  - `ROLLBACK_VERIFIED_PILOT` for rollback.

The workflow refuses any mismatch.

## Verified-artifact requirement

The workflow uses GitHub's API to read `verify_run_id` and requires:

- workflow name exactly `Verify pilot`;
- conclusion `success`;
- `head_sha` exactly equal to `target_sha`;
- event `push`; and
- head branch equal to the repository default branch.

This means PR-only verification runs cannot be released.

The workflow then downloads that run's existing `pilot-verification` artifact using `actions/download-artifact@v4`.

It does not:

- check out source;
- run `npm ci`;
- rebuild Astro;
- regenerate data; or
- modify Git history.

CI builds and verifies two static outputs from the same commit and public-data snapshot:

- `dist/`: domain-root hosting (`/`);
- `dist-pages/`: the free GitHub project path (`/us-national-park-trip-readiness-tracker/`).

Deployment uses the exact matching output retained in that verification artifact.

## Artifact boundary

Before upload, the workflow requires:

- `_verified/dist/index.html`;
- `_verified/dist/build.json`; and
- no symlinks anywhere under `_verified`.

The selected output also requires its own `index.html` and readable object `build.json`. Its `code_commit` must equal the requested `target_sha`. Only the selected static directory is passed to `actions/upload-pages-artifact@v3`; screenshots, lockfiles and the other build are excluded.

## GitHub Pages path matching

Internal navigation uses Astro's configured base path, and Astro prefixes bundled scripts/styles. External NPS links and fragment links retain their destinations. The manifest records the exact `base_path`.

The normal GitHub project Pages URL for this repository uses:

`/us-national-park-trip-readiness-tracker/`

CI checks every generated page, internal destination and bundled asset under both paths. Four project-path Chromium checks cover navigation/search, entry/checklist interaction, footer/fragment navigation, all 14 pages and metadata. Both builds preserve noindex and the same public-data snapshot ID. Project browser results use `test-results/pages` to preserve the root suite's visual evidence; CI checks that the three root mobile/200% text screenshots survive before artifact upload.

The release workflow reads `actions/configure-pages@v5`'s `base_path`, normalizes the trailing slash, and selects `dist` for root hosting or `dist-pages` for project hosting. A missing output, mismatched manifest path or mismatched commit fails before upload. It does not rewrite or rebuild an artifact.

Earlier verification artifacts lacking `base_path` remain root-only candidates, provided their commit matches. They cannot be released at the project URL. A custom domain is no longer required by the build.

Local verification (POSIX/WSL shell):

```sh
npm run build
npm run test:site
npm run build:pages
npm run test:site:pages
npm run test:browser:pages
```

`npm run preview:pages` serves the project build at port 4324 and the project path. The browser harness passes `--ignore-lock` so Astro stays in the foreground and Playwright manages its lifetime.

## Permissions

The workflow declares only:

- `contents: read`;
- `actions: read`;
- `pages: write`;
- `id-token: write`.

The deployment target is the standard `github-pages` environment.

## Rollback

Rollback does not modify source history.

To roll back, dispatch the same workflow with:

- `mode: rollback`;
- an older verified default-branch commit SHA;
- that commit's successful `Verify pilot` run ID; and
- `ROLLBACK_VERIFIED_PILOT`.

The workflow deploys that older run's verified static artifact through the same checks.

Current `pilot-verification` artifacts have a **7-day retention**. Therefore this rollback mechanism only covers verified runs whose artifacts still exist. Extending retention is a separate cost/storage decision.

## Indexing and ads

This milestone does not remove any release safeguards.

The verified application still contains:

- page-level `noindex, nofollow`;
- `robots.txt` blocking crawlers; and
- the repository's `_headers` noindex/security directives.

GitHub Pages does not establish that the custom `_headers` file is applied as HTTP response headers, so effective production headers must be tested after an actual deployment. Every page retains meta noindex. A project-path `robots.txt` is not the domain-root robots policy; it must not be counted as a separate crawler block at project hosting. Root hosting retains both the meta and root robots blocks.

Advertising/analytics remain disabled.

## Current state

No Pages release workflow was dispatched while this feature was developed or when the pilot code was integrated into `main` at `3fe0e878b9b33b457497bff5e761dd33cb962b06`. Verify pilot #132 passed on that `main` push.

Project-path code commit `5751fc47218bc5c7f0062a706f38ad8b01be9ae1` subsequently passed Verify pilot #136, run `36657308469`, including all four project Chromium checks and both generated-output suites. No deployment was dispatched by that development increment.

Therefore:

- no live URL was created or changed by this milestone;
- no rollback has been exercised;
- hosting/rollback readiness is `not_checked`, not `pass`;
- indexing remains blocked; and
- PR #1 is merged, but code integration did not perform a Pages release.

A real deployment should occur only after the earlier data/trust gates are deliberately cleared. No live URL or real rollback has been verified by the project-path development tests.
