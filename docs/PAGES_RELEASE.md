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
- `_verified/scripts/verify-pages-live.mjs`; and
- no symlinks anywhere under `_verified`.

The selected output also requires its own `index.html` and readable object `build.json`. Its `code_commit` must equal the requested `target_sha`. Only the selected static directory is passed to `actions/upload-pages-artifact@v3`; screenshots, lockfiles and the other build are excluded.

## GitHub Pages path matching

Internal navigation uses Astro's configured base path, and Astro prefixes bundled scripts/styles. External NPS links and fragment links retain their destinations. The manifest records the exact `base_path`.

The normal GitHub project Pages URL for this repository uses:

`/us-national-park-trip-readiness-tracker/`

CI checks every generated page, internal destination and bundled asset under both paths. Five project-path Chromium checks cover navigation/search, restored directory controls, entry/checklist interaction, footer/fragment navigation, all 14 pages and metadata. Both builds preserve noindex and the same public-data snapshot ID. Project browser results use `test-results/pages` to preserve the root suite's visual evidence; CI checks that the three root mobile/200% text screenshots survive before artifact upload.

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

## Verify the actual hosted release

After GitHub accepts a deploy or rollback, the workflow runs the dependency-free Node 24 verifier retained in that same successful default-branch artifact. It uses the deployment action's returned URL, the selected static directory and the exact requested commit. The verifier is outside both static builds and is never uploaded to Pages. Source checkout, dependency installation, rebuilding and source collection remain unnecessary.

The verifier checks every regular file in the selected public build, including all HTML pages, bundled scripts/styles, images, `robots.txt` and `build.json`. It requests `index.html` files at their real directory navigation URLs. Each HTTP response must be 200 and match the artifact's SHA-256 digest exactly. Manifest commit, snapshot identity and hosting base must match before requests. Stale pages, missing assets, redirects, provider failures and mismatched content fail the release job. HTTPS URLs must be canonical and contain no credentials, query, fragment or nonstandard port.

There are at most three complete attempts, separated by five seconds, to allow short Pages propagation delays. Requests have a ten-second timeout within a two-minute overall network budget. Artifact limits are 128 files, 4 MiB per file and 64 MiB total; symlinks and nonregular files are refused. Provider bodies and exception text are never printed. A failure does **not** undo the deployment: inspect the report and deliberately roll back using an eligible earlier artifact when needed.

`pages-live-verification.json` records success/failure, safe reason, checked URL, mode, exact commit/snapshot/base, completed file/page counts, attempts and check time. The separate `pages-live-verification` artifact retains this report for seven days even when a live check fails. Selected home-page response headers are observations, including null when absent; they are not inferred from `_headers`. `_headers` is the one configuration file excluded from byte comparison. Matching pages preserve the noindex metadata already required by Verify pilot; the project-path robots file still does not establish domain-root crawler policy.

For a read-only recheck after downloading and extracting the successful verification artifact:

```sh
node scripts/verify-pages-live.mjs \
  --directory dist-pages \
  --url https://vasuki8.github.io/us-national-park-trip-readiness-tracker/ \
  --commit EXACT_VERIFIED_40_CHARACTER_SHA --mode deploy
```

Use `dist` and the actual domain-root URL for root hosting, or `--mode rollback` when verifying the rollback target. Exit 0 means the hosted bytes matched this verified artifact at check time; exit 1 means they did not establish a match. An earlier artifact without the retained verifier now fails layout validation **before upload**. Prepare at least two eligible post-change default-branch artifacts before claiming an older-version rollback path is available.

A successful deploy report alone is not a rollback drill, a browser interaction check, source approval or a cleared release-readiness gate. Before marking hosting/rollback reviewed, retain reports for the initial release, a deliberate older-version rollback and restoration of the intended release, plus browser checks at the actual URL. `tracker.release_readiness` continues to report hosting as `not_checked` because it does not ingest those external receipts, including after a separate operator review; there is no automatic report-to-gate promotion.

## Indexing and ads

This milestone does not remove any release safeguards.

The verified application still contains:

- page-level `noindex, nofollow`;
- `robots.txt` blocking crawlers; and
- the repository's `_headers` noindex/security directives.

GitHub Pages does not establish that the custom `_headers` file is applied as HTTP response headers, so effective production headers must be tested after an actual deployment. Every page retains meta noindex. A project-path `robots.txt` is not the domain-root robots policy; it must not be counted as a separate crawler block at project hosting. Root hosting retains both the meta and root robots blocks.

Advertising/analytics remain disabled.

## Current state

The owner-authorized pilot is live at [ParkReadiness](https://vasuki8.github.io/us-national-park-trip-readiness-tracker/). Pages uses `build_type: workflow` with HTTPS enforced.

The current owner-approved release is commit **`fea984937067fc85fde08d506ced719254e0bc48`**, containing integrated [PR #6](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/6) and its documentation-only integration handoff, with unchanged snapshot **`pilot-08efc3ad8281`**. Exact default-branch [Verify pilot #197](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37072908539), job `111056451305`, passed **906 tests** (290 Node, 432 Python, 62 generated-site and 122 Chromium), zero Astro diagnostics, both 14-page builds and retention of all three accessibility screenshots. Both **108 root and 14 project-path browser cases** passed. Artifact **11255867049** has digest `sha256:441ebac553624cbfb4cd07fff0798549a089c823237d128936423950538376c6` and expires **2026-10-09T22:35:29Z**.

[Deployment #5](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/37073863612), job `111059263233`, published that exact artifact and verified **22 public files and 14 pages in one attempt** at **2026-10-02T22:42:14.981Z**. The successful report binds the project URL, commit, snapshot and hosting base above. The report ZIP was read in memory after its digest and one-file layout were separately checked. Report artifact **11256077822** has digest `sha256:3c2a8751277cc07238ec5957701a31c6857f42ef5ec53568fc9713ef89790dae` and expires **2026-10-09T22:42:16Z**. Independent audit checked the verification ZIP digest, safe layout, both manifests, all 28 artifact pages' noindex metadata and the retained verifier's exact Git blob; the release workflow downloaded the matching artifact digest. All emitted source metadata and stored excerpts match the prior release. No source collection or public-data promotion occurred; original alert observations remain stale and keep their four-hour warnings.

Actual live-browser checks completed at **2026-10-02T22:49:58.130Z**. All 14 pages loaded with noindex and shared light styling, exact **1/0/5/7/4** retained-notice counts, six guidance records and original source clocks. Both directories passed whitespace search, state conjunction and empty/reset counts; a real back return reconciled the actual restored controls. Literal retained-notice search, exact category filtering and reset passed. Dated decision evidence preserved checklist state and focused its exact article; Tab continued to the disclosure and Enter opened the excerpt. Dated and undated correction returns passed that native focus/disclosure path with original clocks and undated limitations. The unsupported-year guard, section-navigation state preservation and trip-edit checklist reset passed. No console warnings/errors were captured. The independent hosted-byte report establishes exact commit/snapshot identity. Provider availability, every browser's restoration/print behavior and screen-reader behavior were not tested.

The **previous live release `696f95868568198ef61f428ee53f765731879983` is the rollback candidate** from successful default-branch [Verify pilot #178](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36889139145), which passed 777 tests. Its artifact **11175802108** was freshly downloaded and checked for matching digest, manifests, layout and noindex pages. It remains available, digest `sha256:9ad38ae23779557f910431e0679d3a9023c3d4de607a0e80c5f4c87f7278a1a6`, through **2026-10-08T16:08:34Z**. No new rollback drill or private recovery checkpoint was performed for this code update; the new report remains in public Actions retention.

For that previous release, [Deployment #4](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36890126850) verified **21 public files and 14 pages in one attempt** at **2026-10-01T16:12:12.182Z**. Report artifact **11175394567** has digest `sha256:7e9d414c09b03ffc3c56cef381f9b3e10759b804f532c6c7e7493f27fb5aa0a8` and expires **2026-10-08T16:12:14Z**. Its actual live-browser checks at **2026-10-01T16:18:13Z** passed all 14 pages/noindex/light styling, exact notice counts and original source clocks, nullable-link notes, both directory filters/empty states/real back return, navigation/history fragments, unsupported-year guidance and checklist toggle/reset/trip-edit reset. No console warnings/errors were captured. Browser navigation to `build.json` was client-blocked; its independent hosted-byte report establishes commit/snapshot identity. Provider availability, forced restoration policies across browsers and screen-reader behavior were not tested.

The original deliberate launch drill for release `303475e260c93f2207e03e08945363cc3ac85882` completed:

1. [Deployment #1](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36807897705): intended release verified at **2026-10-01T02:53:08.921Z**.
2. [Rollback #2](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36808071466): older main commit `df1789da5d634c28ad16329e1f828a042b336a59`, snapshot `pilot-966adad97a6e`, from [Verify pilot #155](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36760287500), verified at **2026-10-01T02:55:24.910Z**.
3. [Restoration #3](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36808199666): intended release restored and verified at **2026-10-01T02:57:09.046Z**.

Each retained live report matched **21 public files and 14 pages in one attempt**. Both release artifacts and all three report ZIP digests/layouts were separately checked and retained in owner-only private operator storage. The final actual-browser check at **2026-10-01T03:00:45.426Z** verified all 14 pages, five park baselines, 17 rendered notices, original clocks, nullable-link notes, loaded styling, search/navigation, the unsupported-year guard and checklist toggle/reset. This is external hosting/rollback evidence; the unchanged automated readiness CLI still reports hosting as `not_checked` because it does not ingest these receipts.

All pages retain meta `noindex, nofollow`; indexing and advertising remain disabled. Observed `X-Robots-Tag`, Content-Security-Policy, X-Content-Type-Options and Referrer-Policy headers were null in the current release report and all three original launch-drill reports. Do not infer those headers from `_headers`, or domain-root crawler policy from project-path `robots.txt`.

The launch drill's older rollback artifact expires **2026-10-07T18:43:32Z**; the previous live release selected above remains eligible until **2026-10-08T16:08:34Z**. Refresh eligible default-branch artifacts deliberately before relying on a later rollback window. Source collection and public-data promotion remain separate manual operations; neither CI nor this release enables a recurring schedule. A later documentation-only handoff commit does not change the artifact already served at the live URL.
