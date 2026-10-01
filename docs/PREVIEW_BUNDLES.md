# Private candidate preview bundles

This is an offline inspection path, not a publisher. It reads verified committed archive observations, freezes current snapshots together with their histories, and builds a separately labeled candidate page. It never substitutes candidate data into the normal Astro build or overwrites `data/`, `public/`, the production `dist/` or `dist-pages/`.

## Prepare a candidate

From the repository root, after dependencies are installed:

```sh
uv run --frozen python -m tracker.preview \
  --archive-dir /absolute/private/alert-staging/archive \
  --output-dir /absolute/private/preview-bundles
```

Use the actual owner-controlled archive location outside the checkout. Keep private files on a Linux/macOS filesystem, or the WSL Linux filesystem on Windows, with the operator runbook's separate `umask 077` session. Native Windows preparation refuses because this boundary requires POSIX ownership and permissions. No key or network request is needed. An absent archive yields explicit never-checked pairs, not successful empty collections. Pending staging receipts are not included. Output reports the exact bundle filename and its content identity, not notice text. Do not put credentials in command arguments or source code.

Every bundle contains the fixed five-park inventory. Each snapshot and its history comes from the same verified per-park chain read. Different parks need not have been checked simultaneously; no global observation time is fabricated. Failed and quarantined checks retain their existing state and original successful-check times.

The output file is canonical UTF-8 JSON named by the SHA-256 of its envelope excluding `bundle_id`. It has purpose `private_preview`, publication false and data kind `unreviewed_source`. The synthetic data kind is for explicit test construction, not source approval. Existing equal candidates are reused without rewriting; different bytes at that filename cause refusal. Files are installed atomically and never overwritten. Maximum bundle size is 10 MiB; the output directory is bounded to 128 entries and 64 MiB, including temporary reservations. No automatic deletion occurs.

The output directory must be absolute, outside the entire checkout and its ancestors, separate from the archive, and contain no symlinks or subdirectories. Its immediate parent must already exist, belong to the current user and have owner-only permissions (`0700`). Preparation creates only the final output directory with `0700`; it does not recursively create parents. An existing output directory must also belong to the current user and be owner-only. Every retained file, including an identical candidate on retry, must be a regular owner-only file (`0600`) with one hard link. Insecure storage is refused without chmod, repair, replacement or cleanup, before a writer lock or output is created. Earlier relative `state/` or `.superpowers/` bundle destinations inside the checkout are now refused; select existing owner-controlled external storage deliberately.

The preparation writer lock is never stolen. After an abrupt process exit, inspect the directory, verify no writer is running and preserve any completed bundle before manually recovering the abandoned lock. An orphan temporary file is not a candidate. A completed filename still has to pass the strict loader; a filename alone is not evidence of validity.

## Build the isolated preview

```sh
mkdir -m 700 /absolute/private/preview-builds
node --experimental-strip-types scripts/build-preview.ts \
  --bundle /absolute/private/preview-bundles/BUNDLE_ID.json \
  --workspace-parent /absolute/private/preview-builds
```

The command requires an explicit input file and an existing owner-only workspace parent on Linux/macOS/WSL. Both must be absolute, outside the checkout and its ancestors, and have no symlink ancestry. The input and its immediate parent must be owner-only; the input must be a single-link regular file. The command validates the canonical envelope and all existing snapshot/history contracts before creating a workspace. Duplicate JSON keys, changed hashes, mixed heads, invented clocks, unexpected fields and unsafe source links refuse. There is no fallback to the committed production dataset or an in-checkout workspace. Create the parent once under an existing private directory; an insecure or missing parent is refused without chmod or recursive directory creation.

A new `run-.../` directory beneath the selected external parent contains the frozen `bundle.json`, cache and separate `dist/`. The build invokes only the installed Astro binary with `preview/` as its root. Its environment is allowlisted: it does not inherit NPS keys, arbitrary Node options or caller-supplied preview locations. The synchronous build child inherits `umask 077`; the caller's original umask is restored on success or failure. Subprocess output is not echoed because diagnostics can otherwise contain unreviewed text. No dependency installation, provider request or deployment is performed by this command.

Astro's working directory is the private workspace, while the driver separately pins the source-project root. This keeps prerender intermediates on the same private filesystem as the output even when the checkout is on a Windows drive. Prerender dependencies are bundled so the external directory does not need dependency symlinks or another installation.

Only a successful build with matching output identity and noindex HTML receives an atomic `ready.json` marker. Readiness checks, including before serving, require owner-only directories and single-link regular files throughout the workspace, with no symlinks, at most 4,096 entries and 64 MiB in total. A zero exit code alone is insufficient. An interrupted or refused attempt is left unready; earlier workspaces are not overwritten. Retry creates another isolated workspace. Creation refuses when the selected parent already contains 64 entries; inspect and remove owned disposable builds explicitly rather than relying on automatic pruning. Old in-checkout workspaces are no longer accepted. Rebuild from a valid external bundle; do not move or alter retained evidence automatically.

To inspect a successful build locally, use the exact workspace returned by the build command:

```sh
umask 077
PARK_PREVIEW_WORKSPACE="<absolute-workspace-path>" npx --no-install astro preview --root preview --host 127.0.0.1 --port 4323
```

The preview config verifies the ready marker before serving. Do not expose the server publicly. `noindex` is not access control. This path is validated on the Linux CI environment; Windows shell syntax and filesystem durability are not established. Directly invoking a development server is disabled for this root. Deliberately overriding CLI paths or modifying trusted build code is outside this guardrail model.

## What the preview shows

The candidate/not-published warning is visible above every park. Each section combines current feed records and the production `HistoryTimeline` component, including original before/after evidence and check timestamps. Empty, failed, quarantined and stale states remain distinct. No changes to date rules, editorial reviews or source timestamps are made. Source text is escaped, never executed as HTML. Notice links use the same provider-supplied label and no-referrer policy as the public pages; a missing URL displays an explicit note without an anchor or invented destination.

Only the candidate page and small `preview.json` metadata are served; the bundle input and private archive are not the web root. Candidate metadata identifies each park's head but contains no archive paths, raw responses or pending receipts. The existing production build remains unchanged, including empty public histories.

## Trust and release limits

After inspecting the exact bundle and preview, the offline [alert-data patch preparer](ALERT_DATA_PROMOTION.md) can prepare the matching public snapshots/history for deliberate operator review. Its optional archive-backed check verifies full committed chains when the bounded preview omits the public checkpoint or new changes; the public omission labels remain. It writes only a private patch outside the checkout and never applies it or approves the data.

A valid digest proves consistency, not authenticity, publication rights or approval. A ready marker describes completion of this local build only. It is not a release, source-verification result, field-conditions audit, or hardware power-loss guarantee. Trusted local filesystems and trusted application dependencies are assumed; hostile same-user mutation, network filesystems and deliberate operator path overrides are not covered.

Live NPS compatibility, source-content review, persistent archive storage, source-change review and production publication/rollback remain separate requirements. No scheduler, hosting setup, accounts, ads or indexing is enabled. Synthetic fixtures remain under tests; their browser harness uses temporary external input/build parents and removes the build workspace after its server exits. Existing CI does not upload private candidate bundles or preview outputs.
