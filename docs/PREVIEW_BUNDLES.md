# Private candidate preview bundles

This is an offline inspection path, not a publisher. It reads verified committed archive observations, freezes current snapshots together with their histories, and builds a separately labeled candidate page. It never substitutes candidate data into the normal Astro build or overwrites `data/`, `public/` or the production `dist/`.

## Prepare a candidate

From the repository root, after dependencies are installed:

```sh
uv run --frozen python -m tracker.preview --archive-dir state/staging/archive --output-dir state/preview-bundles
```

Use the actual owner-controlled archive location. No key or network request is needed. An absent archive yields explicit never-checked pairs, not successful empty collections. Pending staging receipts are not included. Output reports the exact bundle filename and its content identity, not notice text. Do not put credentials in command arguments or source code.

Every bundle contains the fixed five-park inventory. Each snapshot and its history comes from the same verified per-park chain read. Different parks need not have been checked simultaneously; no global observation time is fabricated. Failed and quarantined checks retain their existing state and original successful-check times.

The output file is canonical UTF-8 JSON named by the SHA-256 of its envelope excluding `bundle_id`. It has purpose `private_preview`, publication false and data kind `unreviewed_source`. The synthetic data kind is for explicit test construction, not source approval. Existing equal candidates are reused without rewriting; different bytes at that filename cause refusal. Files are installed atomically and never overwritten. Maximum bundle size is 10 MiB; the output directory is bounded to 128 entries and 64 MiB, including temporary reservations. No automatic deletion occurs.

The output directory must be separate from the archive, not inside protected source/website/Git paths, and contain no symlinks or subdirectories. The preparation writer lock is never stolen. After an abrupt process exit, inspect the directory, verify no writer is running and preserve any completed bundle before manually recovering the abandoned lock. An orphan temporary file is not a candidate. A completed filename still has to pass the strict loader; a filename alone is not evidence of validity.

## Build the isolated preview

```sh
node --experimental-strip-types scripts/build-preview.ts --bundle state/preview-bundles/<bundle-id>.json
```

The command requires an explicit file. It validates the canonical envelope and all existing snapshot/history contracts before creating a workspace. Duplicate JSON keys, changed hashes, mixed heads, invented clocks, unexpected fields and unsafe source links refuse. There is no fallback to the committed production dataset.

A new `.superpowers/preview-builds/run-.../` workspace contains the frozen `bundle.json`, cache and separate `dist/`. The build invokes only the installed Astro binary with `preview/` as its root. Its environment is allowlisted: it does not inherit NPS keys, arbitrary Node options or caller-supplied preview locations. Subprocess output is not echoed because diagnostics can otherwise contain unreviewed text. No dependency installation, provider request or deployment is performed by this command.

Only a successful build with matching output identity and noindex HTML receives an atomic `ready.json` marker. A zero exit code alone is insufficient. An interrupted or refused attempt is left unready; earlier workspaces are not overwritten. Retry creates another isolated workspace. There are at most 64 workspaces under the default parent; inspect and remove owned disposable builds explicitly rather than relying on automatic pruning.

To inspect a successful build locally, use the exact workspace returned by the build command:

```sh
PARK_PREVIEW_WORKSPACE="<absolute-workspace-path>" npx --no-install astro preview --root preview --host 127.0.0.1 --port 4323
```

The preview config verifies the ready marker before serving. Do not expose the server publicly. `noindex` is not access control. This path is validated on the Linux CI environment; Windows shell syntax and filesystem durability are not established. Directly invoking a development server is disabled for this root. Deliberately overriding CLI paths or modifying trusted build code is outside this guardrail model.

## What the preview shows

The candidate/not-published warning is visible above every park. Each section combines current feed records and the production `HistoryTimeline` component, including original before/after evidence and check timestamps. Empty, failed, quarantined and stale states remain distinct. No changes to date rules, editorial reviews or source timestamps are made. Source text is escaped, never executed as HTML.

Only the candidate page and small `preview.json` metadata are served; the bundle input and private archive are not the web root. Candidate metadata identifies each park's head but contains no archive paths, raw responses or pending receipts. The existing production build remains unchanged, including empty public histories.

## Trust and release limits

A valid digest proves consistency, not authenticity, publication rights or approval. A ready marker describes completion of this local build only. It is not a release, source-verification result, field-conditions audit, or hardware power-loss guarantee. Trusted local filesystems and trusted application dependencies are assumed; hostile same-user mutation, network filesystems and deliberate operator path overrides are not covered.

Live NPS compatibility, source-content review, persistent archive storage, source-change review and production publication/rollback remain separate requirements. No scheduler, hosting setup, accounts, ads or indexing is enabled. Synthetic fixtures and previews stay under tests and ignored workspaces; existing CI does not upload private candidate bundles or preview outputs.
