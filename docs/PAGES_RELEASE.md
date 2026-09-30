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

Deployment therefore uses the exact `dist/` that was already verified.

## Artifact boundary

Before upload, the workflow requires:

- `_verified/dist/index.html`;
- `_verified/dist/build.json`; and
- no symlinks anywhere under `_verified/dist`.

Only `_verified/dist` is passed to `actions/upload-pages-artifact@v3`.

## GitHub Pages base-path guard

The current Astro output and navigation use root-absolute URLs such as `/parks/` and root asset paths.

The normal GitHub project Pages URL for this repository would use a base path such as:

`/us-national-park-trip-readiness-tracker/`

Deploying the current artifact there would break root-absolute navigation/assets.

The workflow therefore runs `actions/configure-pages@v5`, reads its documented `base_path` output, and **refuses any nonempty base path before upload/deployment**.

A real release currently requires Pages root hosting—for example, a correctly configured custom domain—or a future code change that makes the entire site base-path aware and re-verifies that output.

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

GitHub Pages does not establish that the custom `_headers` file is applied as HTTP response headers, so effective production headers must be tested after an actual deployment. Meta robots and `robots.txt` remain independent indexing blocks.

Advertising/analytics remain disabled.

## Current state

No Pages release workflow was dispatched while this feature was developed or when the pilot code was integrated into `main` at `3fe0e878b9b33b457497bff5e761dd33cb962b06`. Verify pilot #132 passed on that `main` push.

Therefore:

- no live URL was created or changed by this milestone;
- no rollback has been exercised;
- hosting/rollback readiness is `not_checked`, not `pass`;
- indexing remains blocked; and
- PR #1 is merged, but code integration did not perform a Pages release.

A real deployment should occur only after the earlier data/trust gates are deliberately cleared and the root-hosting/base-path requirement is resolved.
