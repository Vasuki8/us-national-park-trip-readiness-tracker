# Project status and handoff

Updated: **October 1, 2026 (Toronto time), after provider directory-URL validation repair**.

## Current development handoff

Continue on **`codex/manual-refresh-verification`** in [PR #5](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/5), based on integrated main `151e942ec047f746d1288592b6a2bf12d261f0c9`.

The current increment repairs Python collection/archive validation of safe provider directory URLs ending in one slash, matching the existing TypeScript contract. Validation only adjusts the decoded-path comparison; accepted URL bytes and normalized-record hashes are retained. Decoded leading `//`, repeated separators, traversal and backslashes remain refused. `parkCode` remains authoritative, and nullable, shared NPS and safe external links retain their existing contracts.

Six Python regressions cover accepted root/directory/query/fragment URLs, exact hashes and unchanged clocks, archive validation and staged quarantine retention. They first reproduced 22 failing subcases and then passed all 73 focused tests. Four cross-language regressions run actual synthetic collection/staging, immutable evidence and fresh archive replay through snapshot/history/preview and in-memory promotion validation. Unchanged/edited URL history and failed/quarantined attempt clocks are checked; rehashed unsafe counterparts still refuse. The exporter uses disposable external storage, blocks network access and preserves synthetic labels; the preparer refuses those labels before separately testing a simulated envelope. No real approval or publication is established.

Fresh local verification passed **217 Node + 430 Python + 44 generated-site tests = 691 tests**, strict changed-file TypeScript, zero Astro diagnostics and both 14-page builds. Independent review found no actionable issues; its read-only Python/Node probe checked 3,613 decoded-path variants without acceptance mismatches, confirmed external fixture cleanup and retained nullable/external/shared/cross-park/root-link behavior. Exact implementation head `c52fd069eaae16af0338cc388483f6a0ae3f1511` passed [Verify pilot #175](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36820077143): **775 tests**, including **79 root + 5 project-path Chromium tests**, both builds, zero Astro diagnostics and all three retained accessibility screenshots. Artifact `pilot-verification` is `11143755030`, digest `sha256:1bd3a1c56ae6a12d14e72ca6fcf58401c16fa036f567081463c0d8069e1c884a`, retained through **October 8, 2026 at 05:32:38 UTC**. The following handoff-only commit preserves this implementation; check its current-head CI before integration. Local browser execution remains unavailable on Ubuntu 26.04.

The preceding directory increment synchronizes directory cards, result counts and empty-state text with prefilled/restored search and state controls. Initialization and input/change events update immediately; page-return handling queues the update after `pageshow` because persisted form restoration can follow the event. Unchanged result counts do not rewrite live-region text. Seven tests execute the actual script with synthetic controls and queued tasks; two root browser cases and one project-path case cover both directory routes and restoration ordering. The application adds no persistence or transmission of selections.

The shared POSIX editorial file guard now checks canonical containment after its existing raw-path, lexical checkout and symlink checks. Doubled-leading-slash checkout/ancestor aliases refuse before private JSON or ledger access. External aliases retain owner-only JSON, SQLite ledger, backup/restore and preview operations. Error ordering, permissions and single-link requirements remain unchanged; no retained real storage is read, migrated or repaired by this increment.

The preceding local verification passed **213 Node + 424 Python + 44 generated-site tests = 681 tests**, strict changed-file TypeScript, zero Astro diagnostics and both 14-page builds. Directory regressions first produced five expected failures; the later event-order regression failed before the queued correction. Five new editorial path tests produced ten expected failing subcases before canonical checking. Independent review reran all seven directory and five path regressions, external alias backup/restore/preview and refusal-order probes, with no remaining findings. Exact implementation head `3f0c7daa2f476b8501c062a33414a2bc922657af` passed [Verify pilot #173](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36818355841): **765 tests**, including **79 root + 5 project-path Chromium tests**, both builds and all three retained accessibility screenshots. All three new directory browser cases passed. The following handoff-only head `1656bb254e01267bf9fd319081ab37df3296c7c0` passed the same 765 tests in [Verify pilot #174](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36818638591). Those results precede the directory-URL repair. The browser cases emulate event-order restoration and do not establish every browser's restoration policy or screen-reader behavior.

The preceding repair requires absolute private alert archive/staging destinations outside the entire checkout and its ancestors. One shared guard rejects raw traversal and symlink ancestry, then checks canonical containment before storage operations or collection requests. Relative roots, ignored/unlisted checkout folders and Linux doubled-leading-slash checkout aliases are refused. The active runbooks use external absolute paths; old stores are not automatically read, moved, deleted or repaired. Owner-only WSL setup and backup remain separate operator responsibilities.

Trip decisions now replace live-region text only when the displayed result changes. Minute/visibility refreshes still recalculate freshness, including the exact seven-day expiry, and trip edits still reset the checklist. Two tests execute the actual script with synthetic page/clock inputs; a new browser regression observes actual decision-text mutations.

Before the current increment, final PR head `45b3b300072162a130cb9c2993a38c3b6cf4745c` passed [Verify pilot #172](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36816742832): **206 Node + 419 Python + 44 generated-site + 81 Chromium tests = 750 tests**, both 14-page builds, zero Astro diagnostics and all three retained accessibility screenshots. That earlier result does not verify the new directory/editorial changes.

The preceding repairs in this PR corrected informational pages to describe reviewed manual alert/history updates, the four-hour alert freshness window, unscheduled collection and the actual GitHub Pages host. The obsolete claims that no public alerts/history exist or hosting awaits launch are removed.

Generated-site and browser checks follow the current paired history instead of assuming five first baselines forever. Exact metadata, observation clocks/order, visible counts, conditional baseline explanations and omission disclosures remain checked. A real Astro component regression accepts the existing later, bounded, failed and uncollected synthetic histories and rejects corrupted clocks/counts/disclosures. Public release verification still requires the successful public pilot snapshots under the existing release contract; truthful degraded fixture rendering does not clear release eligibility.

Browser scenarios now use a reference after every known review, attempted-check and successful-check timestamp, preserving each park's independent freshness. Annual guidance scenarios use their selected review clocks separately from alert refreshes. Seven synthetic regressions cover alert-only updates after guidance expiry, partial refreshes, later failed attempts, nullable successes and invalid clocks. Before the latest repair, head `0233d696502247808c3a75ce230d9d1cb0e4af5d` passed [Verify pilot #170](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36814213525): **204 Node + 415 Python + 44 generated-site + 80 Chromium tests = 743 tests**, both 14-page builds, zero Astro diagnostics and retention of all three accessibility screenshots. That earlier result does not verify the new destination and trip-result changes.

This increment performs no real collection, public-data promotion or deployment. Public data and its original clocks are unchanged, and the live artifact below remains the hosting baseline. Next: deliberate integration/release review of PR #5 after checking its current-head CI. Future data updates continue through the private collection/review/backup and paired-promotion runbooks; indexing, advertising and recurring operations retain their separate operator decisions. The PR artifact is not an eligible default-branch Pages release artifact.

## Live pilot and integrated main baseline

**Live pilot:** [ParkReadiness](https://vasuki8.github.io/us-national-park-trip-readiness-tracker/) serves verified commit **`303475e260c93f2207e03e08945363cc3ac85882`**, integrated by [PR #4](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/4). The owner-approved eight-file promotion contains six reviewed guidance records and **17 retained notices** (Yosemite 1, Rocky Mountain 0, Yellowstone 5, Zion 7, Grand Canyon 4), with one paired baseline per park. The alert observation time remains **2026-10-01T00:20:43.666438Z**; guidance review time is **2026-10-01T01:18:28.701Z**. Unknown publisher-update and publication timestamps remain null. Deployment reused the verified artifact without rewriting its manifest or source clocks.

The exact main commit passed [Verify pilot #167](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36807575240): **196 Node + 415 Python + 42 generated-site + 80 Chromium tests = 733 tests**, zero Astro diagnostics, both 14-page builds and screenshot retention. The unchanged mobile accessibility regression now passes after allowing long provider heading tokens to wrap. Independent review found no remaining issues. Artifact `pilot-verification` is **11137734399**, digest `sha256:efd5c2ef60e6082ebb3aafaed53ee0d777ec1b4339245b3f6835e9f6128e8910`, retained through **October 8, 2026 at 02:51:50 UTC**. The following documentation handoff does not deploy a different commit.

Pages is configured for the manual Actions workflow with HTTPS enforced. [Initial deployment #1](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36807897705), [rollback #2](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36808071466) to older verified main `df1789da5d634c28ad16329e1f828a042b336a59`, and [restoration #3](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36808199666) all passed. Each report matched **21 public files and 14 pages in one attempt**, excluding `_headers`. Actual browser checks after restoration passed all 14 pages, five populated park baselines, exact notice counts/clocks, missing-link notes, search/navigation, the unsupported-year guard and checklist toggle/reset. All pages retain `noindex, nofollow`. Observed `X-Robots-Tag`, CSP, nosniff and referrer-policy response headers were null; `_headers` is not counted as an applied GitHub Pages policy, and project robots does not establish domain-root crawler policy.

The current public guidance matches the explicitly reviewed private ledger; the verified separately recovered backup matches its head. A read-only provider preflight at **2026-10-01T02:32:53–55Z** passed all five parks. The provider/freshness and hosting/rollback evidence has now been separately assessed and retained with the owner-authorized launch receipts in private storage. The conservative readiness CLI still reports those external checks as `not_checked`, because it does not ingest such receipts; no validator or gate was changed to manufacture a pass. Indexing and ads remain disabled.

**Next milestone:** continue on `main` with deliberate private collection/review/backup and paired public-data promotions when updates are needed. There is **no scheduled collection or automatic deployment**. Alert freshness expires after four hours; guidance review expires after seven days. Preserve original evidence clocks and the existing stale/empty-feed limitations. Indexing, ads and recurring operations require their separate operator decisions. Reuse `docs/DURABLE_COLLECTION_SESSION.md` and `docs/PAGES_RELEASE.md`; artifact rollback currently has seven-day retention. The notes below are historical and do not override this handoff.

### Earlier implementation evidence

**Current increment:** the private alert preview now matches the public pages when NPS provides no notice URL: it shows an explicit missing-link note without an anchor or invented destination. Supplied links use the provider-supplied label and the existing no-referrer policy. The preview snapshot type now admits `null`, matching the validated data contract. The real synthetic exporter includes a nullable current URL, and the existing browser scenario covers missing and supplied links. An actual build/browser regression failed before the fix (no missing-link note and one unusable anchor) and passed afterward. All **195 Node tests**, **22 focused Python preview tests**, strict TypeScript and Astro check with zero diagnostics pass. Independent review found no remaining issues. Code head `65f1aac3324021334f4b2fac92883c2bb891f791` then passed [Verify pilot #163](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36804169524): **728 tests**, including both Chromium suites, both 14-page builds and screenshot retention. The following handoff change records that exact code result; it performs no public-data application or release.

The preceding external-workspace code head `b4099d4e2515054283f6a9308c8f3424366aa472` passed [Verify pilot #162](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36802453288): **195 Node + 415 Python + 40 generated-site + 78 Chromium tests = 728 total**, both 14-page builds, zero Astro diagnostics and retained accessibility screenshots. A read-only GitHub check confirmed Pages is not configured. The release workflow audit found no code blocker; follow `docs/PAGES_RELEASE.md` for deliberate configuration, eligible default-branch artifacts, deployment and rollback verification after approved public data is integrated. Public data, hosting settings, indexing and ads are unchanged by this preview correction.

**Latest development handoff:** `scripts/build-preview.ts` now requires `--workspace-parent` pointing to an existing owner-only directory outside the checkout. It validates private input/workspace permissions and links, builds with private creation permissions, and verifies the complete bounded output tree before marking or serving it ready. Astro runs from that private workspace with a pinned source root and bundled prerender dependencies, so cross-filesystem builds keep candidate intermediates outside the checkout. The synthetic browser harness owns and cleans up its external input/build directories. Operator commands and migration details are in `docs/PREVIEW_BUNDLES.md`.

Fresh external-workspace WSL verification passed **195 Node + 415 Python + 40 generated-site tests = 650 local tests**, strict standalone TypeScript, zero Astro diagnostics and both 14-page production builds. An actual synthetic preview build and loopback HTTP check passed. Independent review passed the 19 focused Node tests and additional permission/link/size probes, with no Critical, Important or Minor findings. Astro's in-checkout generated helpers contain source/type metadata and the loopback server lock only, with no candidate data or private paths. CI #162 subsequently confirmed both Chromium suites for that code head as recorded above. Detailed current operator review, backup and candidate receipts remain exclusively in private storage; follow that handoff for the next deliberate promotion action.

Repository: [Vasuki8/us-national-park-trip-readiness-tracker](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker). **`main`** remains the integrated baseline; continue the proposed launch tooling on **`codex/prepare-live-pilot`**. [PR #2](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/2) is merged at `467ecbe6ddd695132d3e779215554f9852028b53`, preserving all reviewed safeguards and the previously merged [PR #3](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/3) manual NPS-preflight repair. PR #1 is already merged. The branch audit found no unique unpublished code in the nine older local development branches: their complete trees match existing main-history snapshots. The remote foundation branch is already an ancestor of main; the separate preflight branch has the exact content already integrated by PR #3.

Fresh independent review found one footer-notice bypass: `<plaintext hidden />` could pass the source check while Astro expanded it to terminal hidden text consuming the following footer in browsers. The recognizer now explicitly refuses plaintext regardless of parser version. The regression failed before the fix and passed afterward. The correction published as `560e87d1f3d0932b0204e01854bf2897f8266551` has the same tree as local commit `06cf50ed7d4288e61b0de92557dfd7bef738d88e`; the merge tree `05f195189751559552569658626bf83cd2b2686f` was checked against the reviewed current-main/PR candidate. No Critical, Important or Minor review findings remain.

Local consolidation checks passed **399 Python tests**, including all **23 source-rights tests on Python 3.12.3 and 3.12.14**. Before the narrow correction, the combined current-main/PR checkout also passed **158 Node tests**, **40 generated-site tests**, Astro check with zero diagnostics, and both 14-page builds. Independent review reran the focused rights/path/workflow checks and all eight live-verifier Node cases. The prior PR head passed [Verify pilot #150](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36736074852) with 674 tests and retained screenshots.

The exact merged main commit `467ecbe6ddd695132d3e779215554f9852028b53` passed [Verify pilot](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36759197048), job `110037100043`: **158 Node + 399 Python + 40 generated-site + 78 Chromium tests = 675 total**, zero Astro diagnostics, both 14-page builds and screenshot retention. Artifact `pilot-verification` is `11118285148`, digest `sha256:89e5db7cd20e2a2e6548b56daaf19d115995eb342444ffd7352234a447b3e6da`, retained through October 7, 2026. That result covers the merged implementation. The reviewed tooling below is committed on **`codex/prepare-live-pilot`**, based on current local/remote main `df1789da5d634c28ad16329e1f828a042b336a59`, in [draft PR #4](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/4). The repaired implementation head passed all 723 supported-Linux CI tests including both browser suites; no independent review findings remain. Continue with deliberate human source review and reconciliation under the private operator runbook. Main integration and deployment have not occurred.

The local setup and clone/ZIP instructions are in `README.md`; `AGENTS.md` supplies concise project instructions for Codex. Open the actual repository root, use Node.js 24 and Python 3.12+ with uv, run `npm ci` and `uv sync --frozen`, then `npm run dev`. Use a POSIX/WSL shell for the full tests and private evidence tools; on Windows keep private evidence in the WSL Linux filesystem. Ordinary tests use `umask 022`; the private operator runbook uses `umask 077` separately.

**Current proposed increment:** `scripts/prepare-alert-promotion.ts` extends the existing private preview flow with an offline, reviewable Git patch for the five public alert snapshots and their matching history. It reuses the strict bundle/history validators, binds the source bundle and all six public base-file hashes, and installs only an owner-only private patch outside the checkout. Default bounded-preview verification refuses synthetic input, rewinds, forks, missing public checkpoints, changed overlapping observations, cumulative-counter rewinds, altered retained records/clocks and unverifiable new changes. Complete new changes are replayed from the public record state. Exact retries compare raw bytes; invalid UTF-8 public input and unsafe paths/permissions are refused. It neither applies the patch nor approves or publishes data. Operator contract: `docs/ALERT_DATA_PROMOTION.md`.

The optional `--archive-dir` check now handles a public checkpoint outside the 20-observation window or new changes omitted from the bounded preview. The read-only `tracker.alert_promotion_archive` bridge replays each complete committed park chain, projects both exact checkpoints and binds the five-park bundle identity. It accepts an exact frozen prefix of a newer archive, while refusing changed/missing checkpoints and damaged later observations. The existing projection logic is shared after one verified chain read per park. Private archive permissions, disjoint destinations, bounded subprocess I/O and a narrow Python environment are enforced. Public omission counts and source clocks remain intact; archive verification establishes consistency, not human approval, source authenticity, backup or release readiness.

The same command now offers `--check --bundle PATH --patch PATH --candidate-id HASH`, with the original optional archive flag. It regenerates the exact candidate, checks the recorded preparation hash and raw patch bytes, and binds all six current public base files, including unchanged parks. The shared loader preserves bundle/pair/continuity checks; a bounded reader also protects existing-patch retries. Check mode creates no files, applies no patch and reports human review still required. Keep the checkout and private inputs unchanged between this point-in-time check and any separately authorized application. Explicitly supplying an empty archive path now refuses rather than silently falling back to bounded continuity.

**Latest repair:** upstream `tracker.preview.prepare_bundle()` now requires an absolute output outside the entire checkout and its ancestors, with an existing owner-only parent, owner-only output directory and single-link owner-only regular files. The old protected-folder list still allowed unlisted checkout destinations and did not reject readable directories or equal candidate files. The repair reuses the existing POSIX guards, validates retained output before creating its writer lock, creates only the final directory, and performs no chmod, relocation, replacement or cleanup of existing files. Relative `state/` and `.superpowers/` bundle output paths are deliberately refused; use the updated examples in `docs/PREVIEW_BUNDLES.md`. The synthetic browser harness now owns an external temporary input directory and removes it after the isolated build has copied the bundle.

Preview-boundary WSL verification passed **188 Node and 415 Python tests: 603 total**, strict standalone TypeScript checking and Astro check with zero diagnostics. Six new Python regression methods initially produced nine failures and one unsupported-platform error; all 22 focused preview tests now pass. The real exporter Node regression failed against the old in-checkout path and now passes with an owner-only external bundle. The actual synthetic Astro preview build and loopback HTTP probe passed: five parks, matching non-publication metadata, noindex, escaped source text, no pending sentinel, unchanged production bytes and removal of the temporary input. The probe server was then stopped. All new evidence uses disposable synthetic storage and establishes no real capture, review or durability.

Independent preview-boundary review passed all 22 focused Python and 6 Node tests plus probes for retained symlinks, subdirectories, FIFOs and unrelated hardlinks refusing before writer creation, checkout roots/ancestors refusing, and abandoned writer locks remaining untouched. No Critical, Important or Minor findings remain. Browser rendering, hostile concurrent mutation, physical durability and real operator approval remain outside this evidence.

The preceding check-mode increment passed all 29 focused promotion tests; independent review found no remaining findings. Four positive-path tests failed before check mode existed. Its unchanged-park regression demonstrates a stale six-file binding that `git apply --check` alone accepts, and the empty archive-option regression failed before the shared-loader fix. The preceding archive review also independently passed 20 Node and 47 Python tests plus probes for one chain read per park, ignored caller Python settings and damaged observations beyond a frozen candidate.

Launch preparation freshly passed **40 generated-site tests** and both 14-page production builds, alongside the latest 188 Node and 415 Python results (**643 local tests**), strict tool TypeScript and zero Astro diagnostics. Both browser suites remain unavailable locally: Playwright 1.58.2 refused Chromium installation on the available WSL Ubuntu 26.04 runtime (`ubuntu26.04-x64` unsupported). The successful synthetic preview startup probe is not browser-suite verification.

Code head `df9b6246e6a6e39a65103c65be038c689a6deb01` passed [Verify pilot #156](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36777128979), job `110097736722`: **188 Node + 415 Python + 40 generated-site + 78 Chromium tests = 721 total**, zero Astro diagnostics, both 14-page builds and retained root accessibility screenshots. Artifact `pilot-verification` is `11126002339`, digest `sha256:af02cb2b7dd95c187e0852d2d57ca73b7edb2f7d53c8d12414236cf647993fe1`, retained through October 7, 2026. This validates that earlier head; PR-only artifacts remain ineligible for the Pages release workflow.

Final combined review reproduced a bounded-continuity gap: after a successful fetch falls outside both 20-observation windows, an otherwise matching failed/quarantined descendant could rewrite that retained success clock. The repair explicitly binds the candidate clock to the newest new successful observation, or preserves the public clock (including null) if none exists. Two real synthetic `HistoryStore` fixture regressions failed before the guard: a rewound hidden success and an invented first success. All **31 focused preparer/check tests**, the **190-test full Node suite** and strict standalone tool TypeScript checking now pass. Independent combined review reproduced the original preparation/check bypass, reviewed the repair and found no remaining Critical, Important or Minor findings.

Repaired implementation head `c77410fc32bae99fa432abf9c5c698f3c3ae757f` passed [Verify pilot #157](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36778491249), job `110102330424`: **190 Node + 415 Python + 40 generated-site + 78 Chromium tests = 723 total**, zero Astro diagnostics, both production builds and screenshot retention. Artifact `pilot-verification` is `11126536959`, digest `sha256:dfa51182e752e0a521d9ff2c6b4272cc8d1d47b57021bce2fde97fd34c677351`, retained through October 7, 2026. This receipt changes only the handoff; inspect PR #4's current-head checks before integration. This PR artifact is not a default-branch release artifact or evidence of a live website.

Local credential and private operator storage setup are complete. The owner confirmed that the existing NPS key is already configured in GitHub secrets and variables; no new registration is needed. The existing workflow consumes the repository Actions secret named exactly `NPS_API_KEY`, and its five-park keyed preflight already passed as recorded in `docs/NPS_PREFLIGHT.md`. The owner then saved that key privately in WSL. A read-only local check confirmed a regular single-link owner-only file, an owner-only parent with no symlink ancestry, and successful loading into `NPS_API_KEY`; it reported only booleans and made no provider requests. Future operator processes must load the saved file privately; an export in another terminal is not inherited automatically. No key value was printed or added to the repository.

The owner selected a dedicated private GitHub repository for the remote backup. The operator procedure in docs/GITHUB_PRIVATE_BACKUP.md reuses the existing backup/verify/restore tools, requires verified selected checkpoints and a fresh authenticated download/recovery rehearsal, and excludes credentials and public CI artifacts. Local working, transfer and recovery paths retain the existing owner-only POSIX requirements. A local clone is a transfer workspace rather than an independent remote copy. The procedure does not claim client-side encryption or indefinite retention.

Detailed operator handoffs and recovery receipts remain in private storage outside the website checkout. Keep real capture inventories, checkpoint IDs, source-context review state, recovery locations and approval records there. Read the current private handoff for the next operator action; do not copy it into public documentation or a PR description.

The subsequent handoff-only head `38fa6159bd0fc5c70b80a80ef6cbbf05a51fe565` also passed [Verify pilot #158](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36779024069), job `110104121310`, including both browser suites and artifact/screenshot retention. The present operator handoff changes documentation only; implementation and public data remain unchanged.

**The website is still unpublished.** Public data remains unchanged, including the five never_checked alert snapshots. Deliberate source-context review, matching public guidance, reviewed alert promotion and live hosting/rollback checks remain prerequisites. Use the existing readiness command with the current private ledger and downloaded verified backup; retain its operator report privately. No reconciliation, public-data application, deployment, indexing or advertising is performed by this documentation change.

The next priorities for local development are:

1. Follow the current private operator handoff and docs/DURABLE_COLLECTION_SESSION.md. Inspect the complete retained source packets, prepare any corrected guidance inventory with the actual review time, and reconcile only explicitly approved sources using docs/GUIDANCE_RECONCILIATION.md. Refresh packets if the ledger changes. Each new ledger head needs its own verified checkpoint and remote recovery check.
2. Follow docs/ALERT_DATA_PROMOTION.md to review the exact private alert candidate and matching preview, then obtain deliberate public-data application authorization. Retain the reviewed candidate ID and rerun its read-only check immediately before application; refresh collection/candidates when evidence ages or inputs change. Public guidance must separately match the approved private inventory. Keep every private evidence file outside the repository and public outputs. Do not reset history or bypass a refused check.
3. After clearing the required data/trust gates, obtain two eligible successful default-branch artifacts, configure Pages for Actions, and follow `docs/PAGES_RELEASE.md` for explicit deployment, live verification and a deliberate rollback/restoration drill. The expected project URL is not yet a verified live website.

## Historical implementation record

The following notes preserve the implementation evidence and operational details from earlier increments. Branch names, draft-PR states and environment limitations below describe their recorded point in time; the current main handoff above supersedes them.

**Private entry capture now offers an offline setup check before the explicit live run. Release readiness binds public guidance to the reviewed private inventory, source-specific approval hashes and per-source reconciliation provenance, with separate pilot/indexed/advertising targets. Private five-park staging, ledger backup/verify/restore and live capture → reviewer-packet paths remain available. No real durable NPS capture, real ledger backup, or real context approval was performed in this development environment. Public guidance and alert data remain unchanged.**

**The private alert staging, archive-import and candidate-bundle destination guards now also protect `dist-pages/` and its descendants, matching the existing protection for `dist/`. This increment repairs the private/public file boundary introduced by the project-path build. It does not perform real source collection, human review, backup or deployment.**

Repository: `Vasuki8/us-national-park-trip-readiness-tracker`.  
Continuation branch: `fix/protect-pages-private-data`, based on `main` at `25495bdf28d2ab31ddb3198acafca1ffd7d40240`. PR #1 was automatically marked merged after the earlier pilot fast-forward update. No Pages release workflow was dispatched.

## Completed: verify the actual hosted Pages release and rollback

The next development priority is making the five-park pilot live. The existing manual Pages workflow previously stopped after GitHub accepted a deployment. It now checks the actual returned URL against the exact selected verified artifact, for both deploy and rollback, and retains a separate success/failure report. Operator contract: `docs/PAGES_RELEASE.md`; implementation: `scripts/verify-pages-live.mjs`.

Every public regular file except the host configuration `_headers` is compared by SHA-256, including HTML at real directory URLs, scripts/styles, images, robots and the public build manifest. The manifest must match the requested commit and hosting base before network requests. Non-200 responses, redirects, stale/mismatched content, transport errors, unsafe URLs, symlinks and oversized artifacts/responses refuse verification. Three attempts allow brief hosting propagation; ten-second requests run within a two-minute network budget. The report includes commit/snapshot/base, mode, counts and observed home-page headers; absent headers remain null. Matching the verified bytes preserves its existing noindex metadata, but no project robots or custom `_headers` policy is inferred as a domain-wide HTTP control.

Verify pilot now retains the dependency-free verifier outside both static outputs. Pages still uploads only the selected static directory, installs no product dependencies, checks out no source and performs no rebuild or collection. Node setup occurs before deployment. A failed live check fails the job and retains `pages-live-verification.json`; it does not automatically reverse a completed deployment. An artifact predating the retained verifier fails layout validation before upload, so prepare at least two eligible post-change default-branch artifacts for an older-version rollback. PR-only runs remain ineligible; retention remains seven days.

Eight new Node test cases exercise root/project URLs, all file classes, deploy/rollback identity mismatches, HTTP errors/redirects/encoding, propagation retry, invalid URL/manifest inputs, symlinks, size bounds and redacted transport failures. Two new workflow contracts cover URL/artifact wiring, failure reporting and the verifier/public-upload boundary. The tests were observed failing before the new verifier/integration existed. All eight focused cases and **398 local Python tests** passed; independent review found no Critical/Important issues and independently passed eight Node cases plus 19 workflow tests. Network cases use synthetic responses and do not establish a real hosted-site check. The local full npm command still hit the known sandbox subprocess/I/O failures in `build-preview`, `entry-review-store`, `entry-source-extraction` and `preview-io`; full CI passed all Node tests below.

Implementation commit `fb600c53b4705ae6e4cf192017e5448e7003922a`, tree `653e4a165d47dfbecda66843e933fb8220b5d82d`, passed [Verify pilot #149](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36735262681), job `109955241867`:

- **158 Node, 398 Python, 40 generated-site and 78 Chromium tests: 674 total.**
- Astro check: 25 files, zero errors/warnings/hints; root/project builds: 14 HTML pages each.
- Root accessibility screenshot retention passed.
- Artifact `pilot-verification`: `11105954073`, digest `sha256:093b4e1d1f218d23110f03cdc05f38b7068d8f18d80121c7ea6bf89b331d776a`, expires October 7, 2026.

This handoff update follows completed implementation, independent review and successful full CI. Work remains proposed in [draft PR #2](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/2). No Pages workflow was dispatched and no real URL, rollback or source approval was verified. Public guidance/alerts remain unchanged; the pilot report remains **1 pass, 1 blocked, 3 not checked**, and indexing/ads remain disabled. A live-verification report alone does not promote any readiness gate.

### Next work toward launch

1. Complete the real owner-controlled capture, human context review and current-head backup/separate-copy session in `docs/DURABLE_COLLECTION_SESSION.md`. Durable destinations and a local NPS key have not been supplied here; the successful Actions API probe is not public-data publication.
2. Finish a deliberate reviewed public-data promotion path using the existing private archive/history projection, with a reviewable candidate and exact paired snapshots/history. The current projection and private preview do not authorize or perform publication. Keep private captures, ledger, packets, archives and backups outside the repository and hosted site. Preserve the existing collection/review/backup tools rather than rebuilding them.
3. Integrate reviewed launch code into the default branch, obtain successful default-branch push builds and retain two eligible artifacts. Configure GitHub Pages to use GitHub Actions and confirm the actual root/project URL. The expected free project URL is `https://vasuki8.github.io/us-national-park-trip-readiness-tracker/`, not a verified live URL.
4. Once the earlier data/trust gates are deliberately cleared, dispatch the existing manual release with the exact eligible commit/run and confirmation. Inspect the retained live report and browser behavior at that URL. Deliberately roll back to the older eligible artifact, verify it, restore the intended release and retain the reports before claiming hosting/rollback evidence. Review external evidence separately; the read-only readiness CLI still does not auto-accept a deployment receipt.

The preceding source-rights handoff commit `2bfcde4c1595c0fcdb369da5fb614d3a724a44e2` passed [Verify pilot #148](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36730398865), job `109938146513`: **664 tests**, zero Astro diagnostics and both 14-page builds. Artifact `11105186391`, digest `sha256:19ebaffee91e738a543eafa3b85760a7f782a062bfb17b5fefdd2d660ef132bc`, retained that prior verified state.

## Completed: validate guidance before source-rights coverage

The source-rights gate previously built a set of guidance ID/source pairs without first validating its input inventory. It could pass empty guidance with an empty manifest, collapse duplicate/conflicting IDs, accept an unofficial or wrong-park URL when the manifest matched it, or approve a reduced inventory missing a pilot source. These false passes were reproduced using disposable repository copies.

The three-line repair reuses the existing `_guidance_inventory` checker and requires nonempty coverage of every fixed pilot source before rights-manifest evaluation. Guidance must have unique valid IDs and exact park/source bindings. Invalid input returns `blocked` with `public_guidance_inventory_invalid`; a matching edited manifest cannot override it. Valid record/manifest reordering, rights metadata and manifest-policy checks, footer checks and report schema remain unchanged. Operator contract: `docs/RELEASE_READINESS.md`.

Six regression methods produced **20 failing cases** before the repair, covering empty inventories, identical/conflicting/cross-file IDs, nonofficial or mismatched bindings, each missing pilot source and all release targets. The order-preservation case remains accepted. All **22 source-rights tests**, the **396-test local Python suite**, data validation and diff checks passed. Independent read-only review found no issues and independently reran all 22 source-rights tests.

Repair commit `fea95b4d875773a144adffcbd159b79819f89007`, tree `c2afd236649dfbfb2ed63de382581f411fa3d359`, passed [Verify pilot #147](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36729360019), job `109934524323`:

- **150 Node, 396 Python, 40 generated-site and 78 Chromium tests: 664 total.**
- Astro check: 25 files, zero errors/warnings/hints.
- Root and GitHub project-path builds: 14 HTML pages each; screenshot retention passed.
- Artifact `pilot-verification`: `11104206230`, digest `sha256:98a341dccec41088b2a1964d3cc73a88cfc5686e2fb5ac128f29015c3ea1d6ac`, expires October 7, 2026.

This handoff was updated after the repair and full CI completed. Work remains proposed in [draft PR #2](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/2). The actual public inventory remains unchanged at six records and still passes its exact source-rights gate. The pilot remains blocked with required counts **1 pass, 1 blocked, 3 not checked**. No provider request, source approval, public-data publication, deployment, indexing or advertising occurred.

The next real trust milestone remains the owner-controlled session in `docs/DURABLE_COLLECTION_SESSION.md`: durable working/separate backup roots, five-source capture and human review, then private alert staging and reviewed publication. This environment still has no supplied durable destinations or local NPS key. The completed inventory and footer checks should be preserved rather than rebuilt; real capture/backup/review and hosting/rollback evidence remain separate gates.

## Completed: require the public footer notice in release checks

The source-rights gate previously accepted its required government-work notice as a substring anywhere in `Layout.astro`. Reproduction showed that an HTML comment, a hidden span or Astro frontmatter alone could keep the gate passing after the real footer notice was removed.

The gate now uses `tracker/source_notice.py` to recognize literal, unconditional text in one direct-body footer. Frontmatter, source-only contexts, inert/hidden content, dynamic/replacement ancestor attributes, conditional/component markup, default-hidden popovers and duplicate document elements cannot establish notice evidence. Complex or truncated Astro source anywhere is refused before HTML-like comments/strings/attribute expressions can invent a footer. The canonical layout, complete property lookups outside the footer, ordinary inline formatting, whitespace and HTML entities remain supported. Report schema/reasons are unchanged; every release target requires this gate. Operator contract: `docs/RELEASE_READINESS.md`.

Eleven new regression methods extend the source-rights suite from 5 to 16 methods. The initial tests produced **46 failures** against the old substring check. Independent review then reproduced JavaScript comment/template/attribute spoofing, hidden popovers and duplicate document markup; **11 additional failing cases** were reproduced before correcting those gaps. Explicit head/title and comparison-expression subcases also cover the same source-spoofing paths. The final local **390-test Python suite**, data validation and diff checks passed.

Independent follow-up review found no remaining Critical/Important findings and independently passed all 16 source-rights methods plus nine additional probes. Its optional browser probe could not run because bundled Chromium was absent and system Chromium hit a sandbox `setsockopt` denial. This is a conservative source recognizer, not an arbitrary Astro evaluator, computed-CSS visibility audit or proof of deployed output; unfamiliar layouts require review. CI supplies the normal build/browser verification below.

Repair commit `2e315071be82135ab3ae452163547bd7ea6f88c0`, tree `36eda55db035b8c1eb4d6aea64daa8b7fa3c31e0`, passed [Verify pilot #145](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36725117066), job `109919897288`:

- **150 Node, 390 Python, 40 generated-site and 78 Chromium tests: 658 total.**
- Astro check: 25 files, zero errors/warnings/hints.
- Root and GitHub project-path builds: 14 HTML pages each; screenshot retention passed.
- Artifact `pilot-verification`: `11102014924`, digest `sha256:31e60d93c76e04d97846219f991c784cd9f7e5ceb0eb2da34d1e02e0f4d60ca0`, expires October 7, 2026.

This handoff update follows the completed repair and successful full CI. Work remains proposed in [draft PR #2](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/2). The actual pilot is still blocked with required counts **1 pass, 1 blocked, 3 not checked**. Public guidance/alerts, provider credentials, source approvals, deployment, indexing and ads were unchanged.

The next real trust milestone is the owner-controlled capture/review/staging/backup session in `docs/DURABLE_COLLECTION_SESSION.md`. No durable working/backup roots or local NPS key have been supplied to this environment. Preserve the existing capture, ledger, reconciliation, backup and staging tools; do not substitute an ephemeral workspace or repository for the private evidence store. Real human review remains a separate action.

The footer repair's final handoff commit `82918b84b902231c2c99213220fa3a36d2b121c8` also passed [Verify pilot #146](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36725960947): **658 tests**, zero Astro diagnostics, both 14-page builds and screenshot retention. Artifact `pilot-verification`: `11104065177`, digest `sha256:33b24e3219d542fe4b4f7dd6ec9a6fe9d7fbc9ccdce708cf06e12a09bf128c64`.

## New: protect the project Pages output from private alert writes

The GitHub Pages build introduced the publishable `dist-pages/` directory, but the existing private staging, history CLI and preview-bundle destination lists still protected only `dist/`. A synthetic reproduction wrote seven private JSON files beneath a temporary project's `dist-pages/` while the reports still claimed no site-data writes. No real provider data or actual public output was used in that reproduction.

All three existing destination guards now include `dist-pages/`, including nested paths. Single-park and five-park live staging refuse before any provider request or file creation; history imports and private candidate exports refuse before archive/output writes. Allowed owner-controlled destinations and the existing ignored `state/` workflow are retained. No public guidance, snapshots, frontend code, package files or workflows changed.

Three new regression methods cover eight unsafe root/nested cases. All eight cases failed against the original code, then passed with the three-list repair. The 76 affected staging/history/preview tests and the complete **379-test Python suite** pass. Data validation and `git diff --check` also pass.

Independent read-only review found no Critical, Important or Minor findings. The reviewer reran 68 focused Python tests and two additional history-report checks, confirming that the shared history guard refuses before store access. No review changes were needed.

Local verification needs a normal `umask 022`: the cloud shell's `077` converted pre-existing tests' intentionally insecure `0755` fixtures into secure `0700` directories, producing five failures and one cascading error before that environment-only adjustment. The existing `npm test` attempt also encountered baseline local limitations in `build-preview.test.ts`, `entry-review-store.test.ts`, `entry-source-extraction.test.ts` and `preview-io.test.ts`; local Astro dependencies are absent and subprocess I/O differs from CI. The normal frontend/build/browser suite must be verified by the unchanged `Verify pilot` workflow on the proposed branch before integration. These local failures are not claimed as passing checks.

The proposed repair at `ab9c630197300761536f9bb6d44d8e441892c855` passed [Verify pilot #143](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36675415344): **150 Node, 379 Python, 40 generated-site and 78 Chromium tests (647 total)**, zero Astro diagnostics, root/project 14-page builds and screenshot retention. Artifact `pilot-verification` is `11079736068`, digest `sha256:81d7ee6a427f9a42856bd088aa8ac13776dbbe44894ab8b4209ef2cecd52a51a`. This resolves the local frontend/build/browser verification limitations for that exact code commit. The branch remains proposed in [draft PR #2](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/pull/2).

The next real trust milestone remains the owner-controlled durable capture/review/staging/backup session described below. This repair clears no release gate and must not be treated as source review or authorization to publish.

## New: checked durable collection runbook

`docs/DURABLE_COLLECTION_SESSION.md` now joins the existing operator contracts into one first-session sequence: choose durable private working/separate backup roots, check offline setup, capture five entry sources, verify a backup and a second copy before human review, reconcile actual reviewed guidance, back up the new head, collect alerts privately, inspect recovery state and read release gates.

A disposable synthetic rehearsal exercised the real CLI setup/status/backup/verify/restore/readiness commands and the existing live operator with mocked transport. It produced five packets and six unresolved holds, verified both backup copies, restored the exact original ledger state, checked all five offline alert summaries without creating staging files and left public data byte-for-byte unchanged. The readiness report remained blocked. No real source requests, review approvals or durable-storage evidence were created. Temporary rehearsal files were discarded.

The current cloud environment has no local `NPS_API_KEY` and no supplied owner-controlled durable working/backup destination. The GitHub Actions secret is not a local credential. The real session still requires those storage choices and the owner's human review; the runbook does not clear a release gate.

The runbook commit `7d20ad06764b79222c55dc6918e3b909a0e508ef` passed [Verify pilot #144](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36720210942): 150 Node, 379 Python, 40 generated-site and 78 Chromium tests (**647 total**), zero Astro diagnostics, both 14-page builds and screenshot retention. Artifact `pilot-verification`: `11098955656`, digest `sha256:de6093dd1c8deb78a69997895f2e11c8647e446cd0bf327f02426d15691a439d`.

The local development commit `679fa089fdddb08c09e976c16afead4c5ecedb2f` was recreated through the connected GitHub app as `3fe0e878`; both commits have the identical tree `b0d120ccd6a353333f7cf244f8dd490c0b8612e4`. The `main` push passed Verify pilot #132, run `36651035959`, job `109684980194`: 148 Node, 328 Python, 18 generated-site, and 74 Chromium tests (**568 total**), Astro check with zero diagnostics, and a 14-page build. Artifact `pilot-verification` is `11070417444`. This integrates code only; it does not satisfy private review, public alert collection, hosting, indexing, or advertising gates.

## Standing product direction

The eventual product remains AdSense-first, light-theme and free of paid-data dependencies. Validate the five-park pilot before expanding to 20 parks. Trustworthy source evidence precedes indexing or advertising. Never infer an all-clear, reopening, permit exemption or annual validity from missing information.

The public build remains 14 HTML pages plus `build.json`, with park/state search, five park pages, date-aware entry guidance, source evidence, checklists, notice history and seven official planning links per park. Yosemite and Rocky Mountain have dated rules; Yellowstone, Zion and Grand Canyon retain undated source observations. Public alert snapshots remain `never_checked`; public histories and the public entry-review register remain empty.

Existing alert collection/archive/staging, candidate previews, visitor history, accessibility repairs, source-change gate, HTML extraction, live entry-page compatibility diagnostic and private review ledger remain in place. Do not rebuild them.

## New: offline private capture setup check

`tracker.entry_review_live --check-only` validates the existing private destination boundaries, replays an existing ledger, checks the expected empty/current head and loads the current guidance inputs. It creates no directories, makes no requests and writes no ledger, packet or public files. The schema-1 metadata report uses `mode: private_entry_capture_preflight` and `setup_validated: true`, with ledger revision/batch/pending-proposal counts, guidance-record count and five required sources. All side-effect flags are false; no source contents or private paths are printed. Exit `0` means setup checked, not guidance approved. Safe refusals exit `2` without a success report.

Live and offline checks share one setup path. Both private parent directories must already exist and be owner-only. The live command previously discovered a missing ledger parent only after requests, and could initialize under an insecure parent. It now refuses both cases before network. `--check-only` and `--live` are mutually exclusive; omitting both still refuses. Existing capture/packet and live exit-code semantics remain intact.

Seven new methods cover empty destinations without creation, real synthetic ledger replay with unchanged SQLite/packet bytes, unsafe destinations, stale/malformed heads, unreadable initial input, mode conflicts and live ledger-parent refusal before requests. The initial RED run produced **14 failing cases**; all **16 focused live-capture tests** now pass. The tests use synthetic captures; no real private storage or source review milestone was cleared.

This is a point-in-time path/head/input-availability check. It does not certify storage durability, backup, source truth, editorial approval, provider compatibility or later writes. Live capture repeats setup validation and the write transaction rechecks the head. The operator contract and example are in `docs/PERSISTENT_ENTRY_CAPTURE.md` and `README.md`.

Independent review found no Critical/Important issues and reran all 16 focused tests successfully. Local verification passed **376 Python, 150 Node and 40 generated-site tests**, zero Astro diagnostics and root/project 14-page builds. Node/site checks used working unrestricted local subprocess I/O. The final GitHub run provides browser checks. The actual pilot remains blocked with required counts **1 pass, 1 blocked, 3 not checked**; indexed/advertising counts remain **1/2/3** and **1/3/3**. This development increment does not perform the owner-controlled real capture, review, backup, alert publication or deployment.

The preceding reviewed-guidance increment on `main`, commit `d378081bc089d9d3d51884219b6c08df5f962ec7`, passed Verify pilot #141, run `36668506696`, job `109738265677`: **369 Python, 150 Node, 40 generated-site and 78 browser tests (637 total)**, zero Astro diagnostics, both 14-page builds and root screenshot retention. Artifact `pilot-verification` is `11077293008`, digest `sha256:b6b3771e35323997834256aa4f699828097aa3192fc1513ea4ad1125ab00dad3`.

## New: bind public guidance to reviewed private records

The durable-review gate previously passed with all five v2 source baselines and zero holds even when public guidance differed from the private reviewed records. It now requires a nonempty, unambiguous inventory; exactly one reviewed baseline per source with exact hashes of that source's private guidance; public/private full-record equality by stable ID; and reconciliation provenance for every current baseline. Summary, dates, exceptions, evidence, review and rights fields are all bound. Record and object-key order do not change identity.

Nine new methods cover changed private guidance, empty/missing/duplicate/extra inventories, absent/wrong/extra approval hashes, duplicate baselines, harmless ordering, safe report output, complete baseline provenance and real synthetic ledger → reconciliation → replay → CLI paths. Initial regressions reproduced **15 failing cases** against the old gate; an additional ordering test could not read the then-absent match evidence. All 29 focused readiness methods pass. The six-record, five-source integration fixture approves only synthetic context, retains approval provenance after a later matching observation, checks both matching and independently edited public JSON, and verifies the report leaves the public files and SQLite ledger unchanged. It is not a real human NPS review.

Independent review also reproduced an inherited provenance gap: four imported v2 baselines could be carried through one source's explicit reconciliation, producing five current v2 baselines and zero holds without reconciling the other four sources. A real synthetic seeded-ledger CLI regression reproduced that pass before the correction. The report now counts only exact current baselines created for sources selected from the preceding event's active register; carry-forward alone cannot satisfy the per-source gate. Full context/hash/timestamp mismatches also block. Seed/import behavior itself is unchanged. Approval provenance is within the replay-verified ledger, not an authentication of the reviewer or an independent check of their assertions.

The report adds only counts and nullable match booleans to the existing schema-2 gate, including `reconciled_v2_sources` separately from the metadata count `approved_v2_sources`. Private records, IDs, paths, context and hashes are not printed. The CLI still replays/verifies the ledger and verifies a supplied backup; direct Python callers must supply already verified evidence. The report never copies private guidance to public data. See `docs/RELEASE_READINESS.md`.

This closes a release-evidence mismatch; it does not clear the real private capture/review, backup, public alert-data or hosting gates. No public data or website activation changed.

Independent follow-up review found no Critical/Important issues and independently reran all 29 focused readiness tests successfully. Local verification passed **369 Python, 150 Node and 40 generated-site tests**, zero Astro diagnostics, and root/project 14-page builds. The Node and generated-site suites used working unrestricted local subprocess I/O; the final GitHub run supplies browser verification. Actual required counts remain pilot **1/1/3**, indexed **1/2/3**, advertising **1/3/3** (pass/blocked/not checked). All targets remain blocked.

The preceding local-link code commit `766f0c008e47c78db8b211106518325c6994ad64` passed Verify pilot #140, run `36665312536`, job `109728613056`: **150 Node, 360 Python, 40 generated-site and 78 browser tests (628 total)**, zero Astro diagnostics, both 14-page builds and retained root screenshots. Artifact `pilot-verification` is `11075238370`, digest `sha256:53d26c763dfab7a1588b5fa7f9253b3a8566a850a00fea04421e014426405e9f`.

## New: complete local static-link coverage

The generated-site gate now scans every emitted HTML page with a dependency-free Python HTML parser instead of the root-relative-only regex. It resolves local `href`/`src` URLs under the domain-root or GitHub project hosting base, including relative destinations, queries and percent-encoded names, and checks local HTML fragment IDs/named anchors. Escaped project paths, missing files and missing fragments fail the existing Node gate. External URLs are skipped without network requests.

Nine regression/characterization methods exercise the real Node gate against temporary outputs under both bases; a tenth exercises the real filesystem checker with older Python parser defaults. The initial six methods reproduced **24 failing subcases** against the old scan, including missed broken destinations/fragments, a newly emitted page and valid external URLs falsely treated as local. The text-element characterization checks that text contents do not supply links or fragment IDs, and an explicit raw/text parser guard preserves this behavior on older supported Python versions. Comments, scripts and inert template contents cannot satisfy a missing fragment; the template element itself retains its normal fragment identity. Both existing 14-page outputs passed the expanded scan with **209 local href/src URLs each**. This closes the earlier Pages review's deferred local-link coverage gap.

Independent review reproduced a trailing-slash normalization gap: regular files requested as directories could pass. Four new root/project cases failed before the fix; trailing-slash local URLs now require directory targets. The older-parser configuration regression also failed before the explicit text-element guard. Review also reproduced Unicode-whitespace URL trimming and suppression of a template element's own ID; six broken-path cases and two valid-template cases failed before those fixes. URL trimming now uses only ASCII C0/space and only template contents are inert.

The helper is a static test utility, not a full browser parser or external-link crawler. It refuses `<base>` elements and covers literal `href`/`src` plus local HTML fragments; `srcset`, CSS URLs, dynamic links and non-HTML fragments remain outside its stated scope. No public data, private source evidence, deployment, indexing or advertising changed. The real private capture/review and hosting gates remain unverified.

Final local verification passed **360 Python tests, 150 Node tests and 40 generated-site tests**, with zero Astro diagnostics and two 14-page builds. The restricted Node run reported subprocess failures in `entry-review-store.test.ts`, `entry-source-extraction.test.ts` and `preview-io.test.ts`; the unrestricted full `npm test` run passed all 150 tests with working subprocess output. Both existing site commands also passed with that access. GitHub CI provides the 78 browser checks and retained screenshot evidence for the published commit.

The preceding readiness handoff at `cf9f62c144fdf0186af0945e5b969b4020bbbdea` passed Verify pilot #139, run `36662854515`, job `109721147012`, including the root screenshot-retention guard. That result covers the **618-test** readiness-target increment.

## New: milestone-specific readiness targets

The report previously required advertising and indexing for a pilot release, contradicting the approved pilot's exclusion of active ads. `tracker.release_readiness` now defaults to `--target pilot` (ad-free and unindexed), with separate `indexed` and `advertising` targets. Durable source review, public alert data, a current verified backup, source rights and hosting/rollback remain required for all three.

All seven gate statuses/evidence remain visible. JSON schema 2 adds `release_target`, per-gate `required`/`required_reason`, and `required_summary`. `blocking` now means required and not passed for the selected target. The full `summary` remains unchanged. Detected ad integration always requires advertising review; removing any pilot indexing control requires indexing review. The report remains read-only.

The actual pilot remains **BLOCKED**, with required counts **1 pass, 1 blocked, 3 not checked**. The one explicit required blocker is uncollected public alerts; missing durable review, backup and live hosting/rollback evidence remain unverified. Disabled indexing and ads are later-target gates. No source/backup/hosting gate was cleared and no website, ads or indexing was activated. See `docs/RELEASE_READINESS.md` for schema migration and the target table.

Eleven additional test methods cover target scoping, a synthetic otherwise-ready ad-free pilot, every failed/unverified core gate, detected ads, partial/complete indexing-control removal, target validation, CLI labels/exit codes and input redaction. The initial regressions failed before implementation. Synthetic READY cases model external core proofs only inside tests; they are not real review approvals.

Independent review found an indexing bypass in the inherited substring checks: commenting out the actual meta tag, limiting robots to a named agent, or narrowing the header path still looked intact. Regressions reproduced that issue and related conditional/component/allow/scoped-header cases. The pilot guard now recognizes active literal head metadata, the canonical wildcard robots group without exceptions, and globally scoped unqualified noindex headers; unfamiliar configurations require review. All 20 focused readiness tests pass. The earlier static link test gap is closed by the increment above.

The final local Python suite passed **350 tests**. The current target reports remain blocked with required counts pilot **1/1/3**, indexed **1/2/3**, and advertising **1/3/3** (pass/blocked/not checked). The Pages code preceding this increment passed exact-head Verify pilot #137, run `36657771103`, at `a14b7430a25bfbb5995d4aecc7a6a902733f3753`, including the screenshot-retention guard; artifact `11073014127` retained both builds and root visual evidence.

The release-target code on `main`, commit `5f3a94a50c2f6f5d37bf02c4a7000f8bf36f7014`, passed Verify pilot #138, run `36662233981`, job `109719292377`: **150 Node, 350 Python, 40 generated-site and 78 Chromium tests, 618 total**, zero Astro diagnostics, and root/project 14-page builds. The screenshot-retention check also passed. Artifact `pilot-verification` is `11074687668`, digest `sha256:3febb905a15504d9fe4d9a5098f1cf0ffc0317d265b3252b2a15dcf758fc30df`. This verifies the report logic and guard regressions, not a real private approval or deployment.

## New: free GitHub project hosting support

The build supports both a domain root and `/us-national-park-trip-readiness-tracker/`. Internal page links, breadcrumbs, directory cards and current-page navigation include the configured Astro base; bundled scripts/styles use the same path. External NPS and fragment links retain their destinations.

CI verifies `dist/` and `dist-pages/` separately and retains both in `pilot-verification`. Each manifest records `base_path`; both outputs use the same public-data snapshot. The manual Pages workflow selects only the output matching the configured Pages path and requested commit, refusing missing or mismatched builds before upload. Older manifests lacking a path remain root-only candidates. Release still deploys an existing verified artifact without rebuilding.

This removes the custom-domain requirement from the code-side hosting path. It does not create a live website, verify rollback, clear private review/collection gates, or enable indexing/ads. See `docs/PAGES_RELEASE.md`.

Code commit `5751fc47218bc5c7f0062a706f38ad8b01be9ae1` passed Verify pilot #136, run `36657308469`, job `109704313944`: **150 Node, 339 Python, 40 generated-site checks (20 per output), and 78 Chromium tests (74 root + 4 project), 607 total**. Astro check returned zero diagnostics; each output built 14 pages. Artifact `pilot-verification` is `11072873775`. Browser behavior is now verified in GitHub CI; local Chromium download remained unavailable.

A follow-up separates the project suite's output into `test-results/pages` so its Playwright cleanup preserves the root suite's screenshots. A local synthetic evidence marker failed preservation before that setting and passed afterward, with the real project HTTP test executed both times. CI now requires all three root mobile/200% text screenshots to remain after the project run and before artifact upload. This is a verification-artifact repair; the generated site and release gates are unchanged.

Independent review found no Critical/Important issues. It separately audited 279 links/assets across all 14 pages per output, including fragment targets, with no missing files, escaped base paths or missing fragments; external destinations matched. The then-deferred query/fragment/relative URL test gap is now covered by the offline local-link gate described above.

## New: five-park private alert staging run

`uv run --frozen python -m tracker.stage collect --live --park all --staging-dir /absolute/private/alert-staging` now checks the existing archive/pending state for all five pilot parks before making a provider request, then collects them sequentially through the unchanged `StagingCollector` receipt and archive path. A pre-existing pending receipt, writer lock or non-advancing clock blocks the batch before network access. A race after precheck can still interrupt the run.

The report contains safe private archive summaries in pilot order. Exit `0` means all five attempts were archived successfully, exit `1` means all five were archived with at least one failed/quarantined check, and exit `2` means a precheck or later execution failed. An interrupted run can have earlier committed parks; the `checks` list reports only those completed commits. Inspect per-park `status` and use offline `recover` for pending receipts before deciding on a new live attempt. The batch is not atomic and does not publish, schedule, review or back up data. See `docs/STAGING_COLLECTION.md`.

Five focused synthetic tests cover successful five-park archival, preflight refusal before network, one provider failure with the remaining parks retained, interrupted partial progress and non-advancing clock refusal. Local verification: **328 Python tests, 148 Node tests, 18 generated-site tests**, Astro check with zero diagnostics, and a 14-page production build. The browser suite could not start its configured history-site web server locally (`astro preview` exited before becoming ready); browser verification requires the GitHub CI environment. No live batch was attempted and the public snapshots remain `never_checked`.

The follow-up `status --park all` reads the five existing per-park summaries without a key, network request, archive write or staging-directory creation. The JSON report preserves pilot order and the existing safe per-park fields; a local read failure returns a generic refusal without a misleading partial report. Four new CLI tests cover empty storage, mixed archived/pending state, error redaction and a later known archive-integrity error. GitHub `main` code commit `00eeb0cb3a8dc2fa5bbe4cb13fb681c40b452b10` passed Verify pilot #134, run `36653736591`, job `109693413426`: **332 Python, 148 Node, 18 generated-site and 74 Chromium tests (572 total)**, Astro check with zero diagnostics, and a 14-page build. The `pilot-verification` artifact is `11071053427`. This is an operator inspection command, not a verified private capture or publication gate.

## New: explicit private reconciliation

The private ledger now supports a fourth write operation, `reconcile`, in addition to `record`, `disposition` and recovery/status operations.

A reconciliation request contains exactly:
- `source_event_revision`: a committed observation event containing the source context the reviewer inspected.
- `proposal_ids`: the active holds being resolved.
- `reviewer` and `rationale`: operator-supplied review metadata.
- `reviewed_at`: the actual editorial review time.
- `records`: the complete resulting private guidance inventory.

Reconciliation is source-level. If a source has multiple active proposals, all of them must be selected; Rocky Mountain's shared source cannot be partially approved. The selected source observation must be the latest retained observation for that source and at least as new as every cleared proposal.

The replacement guidance inventory is validated through the existing rule/note validators. Unaffected records must remain byte-equivalent. Affected records keep the same identity, park and official source, use the exact approved review time, and preserve their existing rights basis and rights-review timestamp. Extra top-level or evidence fields are refused.

The approved excerpt for every affected record must occur exactly once in the retained source context. Missing or duplicated replacement text fails closed. The reconciliation event stores the complete new records plus hashes of the previous and next guidance revisions; prior events remain immutable and reconstructable.

### Reviewed context baseline semantics

Reconciliation derives a persistent **schema-v2 context baseline** from the retained source observation. V2 distinguishes the real editorial sequence: source captured first, then human review/approval. Legacy schema-v1 baselines keep their previous clock semantics.

Subsequent observations automatically consume ledger-held baselines. A caller cannot replace them through a new capture request. When the first explicit reconciliation affects only one source, already-validated legacy baselines for unrelated sources are carried forward rather than silently dropped.

A later matching source observation does not automatically clear a sticky hold. A reviewer may explicitly reconcile from that newer observation if it is the latest retained evidence and the complete source-level hold set is selected.

This is **private editorial approval inside the ledger**, not public publication. The reconcile command does not write `data/`, the website, alert snapshots, public history, deployment state or advertising configuration.

Contract: `docs/GUIDANCE_RECONCILIATION.md` and `docs/ENTRY_REVIEW_LEDGER.md`.

## New: private read-only reviewer packets

`tracker.entry_review_packet` turns one verified ledger snapshot into a deterministic owner-only review packet without network access, ledger mutation, reconciliation, approval or publication.

The operator selects a pilot park and the **latest retained observation event** for that source. Packet generation refuses an unknown/stale event, a source with no retained comparison context, or a source with no active hold.

The packet contains:

- current private approved guidance for the source;
- every active proposal ID that must be reconciled together at source level;
- pending reasons, before excerpts and source-supplied replacement excerpts when present;
- the retained normalized text/H1/link comparison context and context hash;
- exact capture/proposal/review clocks;
- current baseline metadata;
- prior reviewer disposition history; and
- prior reconciliation metadata and old/new guidance hashes.

Dynamic material is escaped. Real `script` elements remain outside the extractor scope; literal script-looking source text is rendered as text. The generated HTML contains no links, images, frames, forms, buttons or scripts and carries a strict Content Security Policy that denies network/connect/object/frame/form activity. Source link targets are shown only as text.

The output directory and packet files are owner-only (`0700` directories, `0600` files) and must live outside the repository under an owner-only parent. Each packet is installed atomically as:

`OUTPUT_DIR/PACKET_ID/index.html`  
`OUTPUT_DIR/PACKET_ID/manifest.json`

The manifest contains metadata/hashes only, including the ledger revision, source event revision, context hash, complete active proposal IDs, guidance hashes and SHA-256 of the HTML. It contains no retained context or private filesystem path. Exact retries are idempotent; a corrupted existing packet is refused rather than overwritten.

A packet is only an inspection snapshot. It deliberately has no `expected_revision` write argument and cannot approve anything. Before a later reconciliation, the operator must re-read the ledger and use its then-current revision.

Operator contract: `docs/REVIEWER_PACKET.md`.

## New: explicit persistent live capture operator path

`tracker.entry_review_live` is the first retained live-entry operator workflow. It reuses the existing fixed NPS transport, source extractor, transactional editorial ledger and read-only reviewer packets; it does not create a second source store.

Before the first network request it requires:

- explicit `--live`;
- an absolute private ledger path accepted by the existing POSIX ledger boundary;
- an absolute packet-output path outside the repository under an owner-only parent; and
- `--expected-revision empty` for a new ledger, or the exact current ledger SHA-256 for a later batch.

A stale expected revision or unsafe packet destination refuses **before network**. The SQLite write still rechecks the expected revision inside its transaction, so a concurrent writer cannot be silently overwritten after capture.

The command then makes one credential-free HTTPS GET to each of the five fixed NPS entry sources using the already-tested transport: no API key, cookies, redirects, retries or arbitrary URL input. Each response remains bounded to 1 MiB and is validated for status, content type/encoding, length and UTF-8 before it can become a successful capture.

All five capture attempts form one complete ledger observation event. Successful raw HTML is retained inside the owner-only SQLite event; failed captures are retained as failed observations rather than discarded or converted into empty success. Existing reconciled baselines are reused automatically. The live append also preserves the latest validated legacy schema-v1 baseline input until explicit reconciliation creates ledger-held baselines, so a later capture cannot manufacture a fresh `context_not_reviewed` hold merely by dropping prior reviewed context. An existing ledger keeps its own current private guidance inventory rather than silently adopting changed repository guidance.

After the ledger commit, the command prepares reviewer packets for every source that has active holds and retained comparison context. A failed source receives no fabricated packet. Packet-generation failures do **not** roll the already committed live evidence back.

Operator command:

```sh
uv run --frozen python -m tracker.entry_review_live \
  --live \
  --store /absolute/private/entry-review \
  --packet-output-dir /absolute/private/review-packets \
  --expected-revision empty
```

For every later run, first use `entry_review_cli status` and replace `empty` with the exact returned revision.

Exit semantics:

- **0** — the complete batch was committed, all five captures succeeded, and every source requiring review has a packet (or no packet is needed).
- **1** — the batch was committed, but at least one capture or required packet is incomplete. This is retained evidence, not a rollback; inspect the safe JSON report and ledger.
- **2** — configuration, validation, stale-write or unexpected failure prevented a normal report. Re-read ledger status before retrying because concurrent/post-commit failures must never be guessed from an exit code alone.

The safe JSON report exposes source URL, HTTP status, capture reason, capture/context hashes, active-hold counts, packet IDs and the committed ledger/source-event revisions. It excludes raw HTML, retained normalized text and private filesystem paths.

This command never calls `reconcile`, never updates public `data/`, never deploys, and never schedules itself. No `NPS_API_KEY` is read or needed.

Contract: `docs/PERSISTENT_ENTRY_CAPTURE.md`.

## New: private ledger backup, verification and restore

`tracker.entry_review_backup` provides an owner-only backup/restore mechanism for the private editorial SQLite ledger. It does not back up public site data and performs no network request, source capture, review decision, reconciliation or publication.

Backup first performs a full ledger replay. It then uses SQLite's backup API to create a transactionally consistent database snapshot in a temporary owner-only directory. The copied database is replayed again and must equal the previously verified logical ledger state before it can be accepted.

A content-addressed manifest binds:

- ledger revision;
- event, guidance-record and pending-proposal counts;
- exact database byte length;
- SHA-256 of the backed-up SQLite database; and
- explicit `network_performed:false`, `approval_performed:false`, and `publication_performed:false`.

The backup ID is SHA-256 over that manifest core. A completed bundle is:

`BACKUP_ROOT/BACKUP_ID/review.sqlite3`  
`BACKUP_ROOT/BACKUP_ID/manifest.json`

Backup roots and files are owner-only and must be outside the repository under an owner-only parent. Exact retries reuse an identical verified bundle. Corrupt/mismatched bundles or unexpected files are refused rather than overwritten.

`verify` checks private permissions, exact bundle contents, manifest identity, database size/SHA-256 and full semantic ledger replay without modifying the backup.

`restore` accepts only a fully verified bundle and only a brand-new destination. It copies into a temporary owner-only ledger directory, replays the restored database, and atomically renames it into place only after the restored head/counts match the backup manifest. Existing destinations are never overwritten. Interrupted backup/restore tests confirm no completed destination is exposed.

Commands and limitations: `docs/ENTRY_REVIEW_BACKUP.md`.

This mechanism makes local backup/restore testable, but it does **not** create an off-host backup service, choose backup media, encrypt the database, authenticate reviewers, certify native Windows/network filesystems, or prove hardware power-loss durability. Those remain operator/storage decisions.

## New: read-only release-readiness report

`tracker.release_readiness` consolidates the pilot launch gates into one deterministic, non-mutating report. It never contacts providers, deploys, changes indexing, enables advertising, writes public/private state, or interprets missing evidence as success.

Default repository-only command:

```sh
uv run --frozen python -m tracker.release_readiness --format text
```

Machine-readable form:

```sh
uv run --frozen python -m tracker.release_readiness --format json
```

When owner-controlled private evidence exists, the report can also replay the private ledger and verify a specific content-addressed backup before evaluating those private gates:

```sh
uv run --frozen python -m tracker.release_readiness \
  --format text \
  --store /absolute/private/entry-review \
  --backup /absolute/private/backups/BACKUP_ID
```

The seven gates are:

1. durable source review;
2. NPS alert API validation;
3. private storage backup;
4. source-rights review;
5. hosting and rollback;
6. search indexing; and
7. advertising readiness.

Status values are only `pass`, `blocked`, or `not_checked`. In schema 2, a non-pass status is release-blocking when its gate is required for the selected target. The default pilot requires the first five gates; unchanged indexing controls and absent ads remain later-target gates.

The current repository-only result is deliberately **BLOCKED**:

- durable source review — `not_checked`: no owner private ledger supplied;
- NPS alert API — `blocked`: all five public snapshots are still `never_checked`;
- storage backup — `not_checked`: no owner private ledger/verified backup supplied;
- source rights — `pass`: the exact six public NPS text uses have record-level metadata and the matching rights manifest; this does not clear broader or future uses;
- hosting/rollback — `not_checked`: a manual verified-artifact deployment path exists, but no live URL or rollback is verified;
- indexing — `blocked` for its later target: repository controls remain intact; not required for the default pilot;
- advertising — `blocked` for its later target: no ad integration is enabled; not required for the default pilot.

The alert gate intentionally never describes `never_checked` snapshots as “no alerts” or an all-clear. If future public snapshots become successful, the static report still returns `not_checked` until freshness/provider compatibility has release evidence rather than self-promoting collection success.

The private source-review gate passes only when the verified private state has schema-v2 reviewed context baselines for all five fixed entry sources and zero pending proposals. The private backup gate passes only when a previously verified backup manifest matches the exact current ledger head and event count.

This report is an evidence summary, not an authorization to launch. Removing `noindex`, adding deployment/ad code, or supplying a private ledger changes individual evidence but does not itself approve release.

Contract: `docs/RELEASE_READINESS.md`.

## New: NPS alert preflight gate hardening

The read-only keyed NPS alert preflight was rerun on the current feature branch after expanding its validation trigger to changes in the workflow, `tracker/preflight.py`, and `tracker/alerts.py`. It remains unscheduled and has read-only repository permissions.

Current run **36607959537**, job **109541744290**, head **16dda2f20c504ada6d9740c1de38f458e47cb7f9**, returned:

```json
{"schema_version":1,"mode":"read_only","status":"not_configured","gate_passed":false,"publication_performed":false,"checks":[]}
```

The runner still received no usable `NPS_API_KEY`, so it made zero provider requests and changed no data. This establishes the current branch configuration state for that execution; it does not expose or directly inspect repository secrets.

The preflight exit contract is now release-gate aligned:

- `verified` / `gate_passed:true` → exit 0;
- `needs_review` → exit 1;
- `not_configured` or `invalid_configuration` → exit 2.

Therefore the current preflight workflow is intentionally **red** while the key is unavailable. A successful Actions job can no longer visually imply that the alert integration is verified when `gate_passed:false`.

The public alert snapshots are untouched and remain `never_checked`; this diagnostic does not publish or stage data. Configure the owner-controlled repository secret named exactly `NPS_API_KEY` before expecting this gate to pass. Do not send the key through chat, issues, or committed files.

Contract and exact run evidence: `docs/NPS_PREFLIGHT.md`.

## New: gated GitHub Pages deployment and rollback path

`.github/workflows/pages-release.yml` adds a production-hosting path without making the site live. The workflow is **manual-only** (`workflow_dispatch`); it has no push, pull-request, or schedule trigger.

Every deployment or rollback requires all four explicit inputs:

- `mode`: `deploy` or `rollback`;
- `target_sha`: an exact lowercase 40-character commit SHA;
- `verify_run_id`: the GitHub Actions run ID containing the verified build artifact; and
- `confirmation`: exactly `DEPLOY_VERIFIED_PILOT` or `ROLLBACK_VERIFIED_PILOT` for the selected mode.

The workflow queries GitHub for that run and refuses unless it is a **successful `Verify pilot` push run on the repository default branch** and its `head_sha` exactly matches `target_sha`. It then downloads that run's existing `pilot-verification` artifact. It does not check out source or run a fresh build during release, so deployment and rollback use the exact static output that already passed verification.

Only `_verified/dist` is repackaged as the Pages artifact. The workflow requires `dist/index.html` and `dist/build.json` and refuses symlinks.

The current verified frontend uses root-absolute links and Astro asset URLs. Default GitHub **project Pages** would serve under `/us-national-park-trip-readiness-tracker/` and would therefore break those URLs. The workflow reads the official `actions/configure-pages@v5` `base_path` output and refuses any nonempty Pages base path **before** artifact upload/deployment. The current build therefore requires root hosting, such as an appropriately configured custom domain, unless the application is later made base-path aware.

The workflow grants only `contents: read`, `actions: read`, `pages: write`, and `id-token: write`. Deployment uses the standard `github-pages` environment and `actions/deploy-pages@v4`.

Rollback is the same artifact path with `mode: rollback` and an older successful default-branch Verify run. It never runs `git revert`, `git reset`, or pushes source changes. The current `pilot-verification` artifact retention is seven days, so this rollback mechanism only covers verified runs whose artifacts have not expired.

No release workflow was dispatched during the implementation or the later `main` integration. PR #1 is now marked merged, and all existing `noindex` controls remain unchanged. `public/_headers` is retained in the build, but GitHub Pages does not by itself establish that those custom response headers are effective; real hosting/header behavior remains part of the post-deployment verification gate.

The release-readiness `hosting_rollback` gate now moves from `blocked` to **`not_checked`**: a deployment/rollback mechanism exists, but no real production URL or rollback has been exercised.

Contract: `docs/PAGES_RELEASE.md`.

## New: exact public NPS text source-rights evidence

`data/source-rights.json` now records the commercial-use evidence for the **exact six public guidance records** and their five NPS source pages. This is deliberately narrower than a claim about all material on NPS websites.

The review is grounded in the current official NPS disclaimer and Arrowhead-use guidance:

- NPS-created material on the NPS website is generally considered public domain unless otherwise indicated;
- NPS asks for source acknowledgement, and commercial republication should include a reference to the original U.S. Government work, such as **“No protection is claimed in original U.S. Government works.”**;
- third-party material must not be assumed public domain; and
- the NPS Arrowhead and other protected marks are not covered by the public-domain rule and require separate authorization.

The manifest therefore allows only:

- the six already-reviewed short NPS text excerpts;
- the project's original planning summaries tied to those records; and
- source attribution/links.

It explicitly records **no third-party material, NPS marks, photographs, graphics, audio/video, or private raw captures** as approved for public reproduction.

`scripts/validate-source-rights.ts` makes exact manifest coverage part of the normal build gate. Omitting or duplicating a guidance record, changing its source URL, claiming marks/media/third-party content, changing the policy URLs, or changing the commercial notice fails validation.

The site footer now includes the commercial U.S. Government-work notice while retaining the existing independent/non-endorsement statement.

The release-readiness source-rights gate now passes only when:

- all six public guidance records retain their record-level rights metadata;
- `source-rights.json` exactly covers all six record/source pairs;
- every covered item remains classified as NPS government text with no third-party/mark/media reproduction;
- the commercial notice is present in the public layout; and
- the public application contains no media asset or reproduced NPS mark/media reference outside this text-only scope.

This **passes the current public-text scope only**. It is not legal advice or blanket clearance for other NPS pages/content. Adding photos, graphics, logos/marks, audio/video, third-party material, or public raw source captures requires a new rights review and evidence update.

Contract: `docs/SOURCE_RIGHTS.md`.

## New: keyed NPS alert API compatibility validated

The owner configured the repository Actions secret `NPS_API_KEY`, and the existing read-only preflight was rerun against live NPS alert responses.

The first keyed request proved authentication was working but exposed collector assumptions that were stricter than the current provider contract. Safe diagnostic mode was added so preflight could report only allowlisted validation reasons—never provider text, credentials, or raw payloads.

Live diagnostics identified:

- Yosemite and Zion alert records with provider-supplied links outside the old hardcoded NPS-host/path rule; and
- a Grand Canyon alert with no direct URL.

The official NPS alert schema documents `url` as a link supplied only **if available**. The collector/history/build contracts were therefore updated so:

- `parkCode` remains the authoritative park-scope field;
- an absent alert URL is normalized to `null`, not invented;
- safe provider-supplied external HTTPS links are retained;
- the UI labels such links as **“More information link supplied by NPS”** rather than implying NPS ownership of the destination; and
- credentials, secret-bearing query/fragment values, malformed/path-traversal URLs, localhost/numeric-IP targets, and NPS-lookalike hosts remain rejected.

The final keyed compatibility run **36628434444**, job **109611267322**, at 2026-09-29T20:44:13–20:44:14Z returned:

- Yosemite — success, 1 record;
- Rocky Mountain — success, 0 records;
- Yellowstone — success, 5 records;
- Zion — success, 8 records;
- Grand Canyon — success, 3 records.

Each park required one page, every diagnostic code was null, `gate_passed:true`, and `publication_performed:false`.

This proves the current keyed NPS API integration/normalization path for the five pilot parks. It does **not** mean the public site is collecting live alerts yet. The public alert snapshots and public history remain untouched/`never_checked`. The next alert milestone is durable private collection/staging and review before any public data publication.

Exact safe evidence: `docs/NPS_PREFLIGHT.md`.

## TDD and self-review record

The reconciliation contract was developed test-first.

- Verify pilot #47 (`36579697560`) failed because `reconcileEntryReview` did not exist.
- Initial implementation exposed a clock-model mismatch between legacy baselines and explicit review-after-capture; schema-v2 baselines were introduced without weakening v1.
- Verify pilot #51 (`36581315199`) reproduced acceptance of extra unreviewed schema fields; exact record/evidence shape is now required.
- Verify pilot #53 (`36581590068`) reproduced rejection of a valid newer matching source observation while an older hold remained; reconciliation now binds to the latest retained source observation.
- Verify pilot #56 (`36582585446`) reproduced loss of an unrelated reviewed legacy baseline when reconciling one source; unaffected latest validated baselines are now preserved.

The final review-focus tests also cover absent and duplicated approved excerpts, partial source-level proposal selections, exact retry, caller baseline override, stale source observations, CLI redaction and unchanged rights metadata.

Review was **author self-review**, not independent approval.

## Earlier implementation verification

Code/test head: **`1ed3731e7590bc9b952276aac757a6c248611569`**.

**Verify pilot #130, run `36637313452`, job `109641517736`, completed successfully.**

| Check | Verified result |
|---|---:|
| Node core/data/review/rights/history tests | 148 passed |
| Python collector/archive/extraction/ledger/reconciliation/packet/live/backup/readiness/Pages/rights/preflight tests | 323 passed |
| Generated-output tests | 18 passed |
| Chromium browser tests | 74 passed |
| **Total automated tests** | **563 passed** |
| Astro check | 24 files; 0 errors, 0 warnings, 0 hints |
| Production static build | 14 HTML pages plus `build.json` |

The keyed-alert compatibility increment was driven by live read-only provider evidence plus synthetic regressions. Initial keyed runs proved authentication worked but quarantined Yosemite/Zion/Grand Canyon. Diagnostic-code tests then failed first before safe allowlisted diagnostics were added. Provider-compatible tests failed before nullable URLs, NPS subdomains, and safe provider-supplied external HTTPS links were accepted across collector, Python/TypeScript history validation, build validation, and rendering.

The earlier regression run #130 passed all 563 automated tests. The later `main` run #132 passed 568, as recorded above. Separately, keyed NPS preflight run **36628434444** passed all five parks with `gate_passed:true`; it used the same collector semantics and performed no public writes.

Verification artifact `pilot-verification`, ID **11064403957**, contains the production site build, screenshots and lockfile—not API credentials, live raw payloads, private archives, or published alert data. CI-reported ZIP SHA-256: `36548eafd4330bec7afb8898a1ef32d2db37ab43585de3f21e53faf701cab1ae`.

Review was author self-review because no independent reviewer/subagent tool is available. No deployment/indexing/advertising/public-alert publication occurred.

## Previously verified real-page compatibility

Diagnostic run `36575873171`, job `109431220513`, captured the five exact configured NPS entry pages on September 29, 2026. All five returned HTTP 200; all body-text/link contexts extracted; all six saved guidance excerpts were uniquely present; temporary ledger replay succeeded.

Every source reason was `context_not_reviewed`, with six temporary holds and **zero approved context baselines**. Those captures were deliberately discarded after the diagnostic. They are compatibility evidence, not a durable reviewed reference archive and not proof that park requirements are unchanged.

Exact safe retrieval metadata and hashes remain in `docs/LIVE_ENTRY_COMPATIBILITY.md`.

## Remaining gates

No real reviewer has used the new reconciliation command on a durable NPS capture. Therefore there are still **zero durable real approved context baselines** created by this workflow.

The private ledger remains owner-only local POSIX storage, not hosted durable storage, encryption, authenticated reviewer identity or multi-host storage. Backup/verify/restore mechanics are now tested, but no off-host target, retention schedule, removable-media policy or cloud backup has been configured. Hardware power-loss, native Windows/network filesystems and hostile same-user mutation remain outside verified guarantees.

The exact six-record public NPS **text-only** rights scope now has explicit evidence and passes its release-readiness gate. This does not clear private raw captures, NPS marks/media, third-party material, or future source uses. Hashes prove internal consistency, not factual truth or source authenticity.

The keyed NPS alerts integration is now **validated**. Read-only run **36628434444**, job **109611267322**, completed with `status: verified` and `gate_passed:true` for all five pilot parks: Yosemite 1 record, Rocky Mountain 0, Yellowstone 5, Zion 8, and Grand Canyon 3. The run wrote no public snapshots or history, so public `data/alerts/*.json` remain `never_checked`. Provider compatibility and public collection/publication remain separate gates.

No scheduler, real deployment, indexing, advertising, tracking, account system, spending or provider agreement was activated. A manual Pages deployment/rollback workflow now exists but was not dispatched. Neither pilot release milestone is declared complete.

## Next coherent task

The code-side private storage gates now include capture, ledger replay, reviewer packets, reconciliation, backup/restore, a five-park alert staging command, and a manual verified-artifact hosting/rollback path. The next trust milestone remains an **owner-controlled real five-source entry-page capture and human review session**, together with a real five-park alert staging run on durable private POSIX/WSL storage. The keyed NPS alert preflight has already succeeded; do not treat it as public collection.

Run `entry_review_live --check-only` on the chosen private paths with the expected empty/current ledger head before the real capture. Both private parents must already exist with owner-only permissions. A successful offline setup report does not perform or approve that capture.

Before reviewing or reconciling real guidance, create a content-addressed ledger backup with `entry_review_backup backup`, run `verify`, and keep a second verified copy on owner-controlled storage separate from the working ledger. Then inspect the generated packets and use `reconcile` only for guidance a human actually approves.

That real session cannot be performed in this development environment because the current tools do not provide the user's durable private POSIX/WSL filesystem or backup destination. Do not substitute GitHub Actions artifacts, repository files or public hosted storage for the editorial ledger/backup.

The keyed NPS alert API compatibility gate is now validated. The batch command makes durable private staging/archive collection easier to operate, but it still needs owner-controlled storage, a real run, backup and review before public snapshot/history publication.

## Verification lineage

Prior communicated totals: 79 foundation; 109 source coverage; 167 private history; 206 staging; 246 visitor history; 293 previews; 309 planning links; 347 accessibility; 380 selected-source gate; 416 extraction; 460 ledger/identity; 488 live entry compatibility; 563 before five-park batch staging; 568 at the initial `main` integration. The offline five-park status increment passed **572 tests** at `00eeb0c`, Verify pilot #134. PR #1 is merged; the site release gates remain blocked or not checked.
