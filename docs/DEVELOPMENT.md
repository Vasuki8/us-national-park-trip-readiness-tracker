# Development guide

## Product direction and operating rules

Read the complete [permanent owner instructions](PROJECT_INSTRUCTIONS.md) and
the current `PROJECT_STATUS.md` handoff before development. National Park
Explorer & Trip Planner includes park discovery, activities, when-to-visit
guidance, detailed planning, named-location weather, conditions and account-free
personal trip tools. The five-phase policy governs the order of work. The
[foundation assessment](FOUNDATION_ASSESSMENT.md) records existing capabilities,
source-contract gaps and the implementation sequence.

Codex owns routine technical decisions, implementation, source processing,
testing, diagnosis and authorized release operations. Escalate consequential
owner decisions as described in the policy, and record material architecture
choices with their evidence. Cloudflare and centralized scheduled collection
are preferred directions to evaluate; the current Astro/GitHub Pages hosting,
manual publication and page-only trip state below describe the implemented
pilot. New infrastructure, weather, imagery and persistent trip tools remain
staged requirements. Historical pilot exclusions do not override the revised
owner scope; current privacy, provenance and release safeguards still apply.

## Structure

`data/parks.json` holds the reviewed pilot inventory, park-specific official URLs and IANA timezones. `data/rules.json` holds annual entry guidance, exact excerpt evidence and rights-review metadata. `data/alerts/*.json` holds the approved public collector state; the first five successful baselines were promoted with owner approval. Historic and synthetic tests use explicit fixtures rather than these mutable public snapshots.

`src/lib/readiness.ts` is the pure clock-injected decision layer. `scripts/validate-data.ts` gates build-time inventory, hashes, timestamp coherence and source scope. `tracker/alerts.py` handles injectable collection, bounded transport and atomic writes. Astro pages/components render meaningful HTML, and small browser scripts handle search and page-only trip choices. Tests use synthetic provider responses, never live network requests.

The legacy `python -m tracker` direct-write command is retired. It returns exit
2 with a static migration message and does not read keys, parse destinations,
request sources or write files. Continue using the explicit private
`python -m tracker.stage` commands and paired reviewed promotion workflow;
there is no second public-data writer.

`tracker/park_profiles.py` is a separate injectable NPS `/parks` normalization
and collection foundation. It retains introductions, official park identity,
category-only activity metadata and clearly typed seasonal weather context.
Missing optional fields remain null; failed or quarantined attempts retain the
last-good profile and successful clock. Its initial profile age policy is 168
hours, independent of alert freshness. The normalizer has no default HTTP
transport, persistence or website consumer.

`tracker/profile_transport.py` adds the separate bounded, header-authenticated
fixed-endpoint request. `tracker/profile_checkpoints.py` retains explicit
immutable all-five checkpoints using existing POSIX private-file guards; no
mutable latest head or history replay is claimed. `tracker/profile_stage.py`
offers deliberate live collection and offline verification, fresh restore and
private review export. It reads a key only after validating storage, baseline,
clock and the output lock. Review export keeps source rights not checked,
approval false and source/publication clocks unchanged. See
[PROFILE_COLLECTION.md](PROFILE_COLLECTION.md) for limits, interruption and
backup boundaries. Real profiles, their text-use scope, remote recovery,
reviewed public promotion and frontend consumption remain subsequent work.

Each park page has native "On this page" navigation after its introduction. Fragment links reach the conditions snapshot, entry check, checklist, stored guidance, notice history and official planning checks; the retained-notices item appears only when that collection exists. Destinations use `tabindex="-1"` for keyboard focus and subsequent Tab navigation. The collection link preserves current notice filters, while existing exact article links keep their reveal behavior. This menu works without JavaScript, wraps when text is enlarged and is hidden in print. It adds no script, storage or requests, and section jumps do not submit entry decisions, mark checklist items or change source metadata.

The park directory applies the current search and state values on initialization and after page return (`pageshow`), as well as normal input/change events. Literal substring search trims, lowercases and collapses whitespace in both the query and card search text, so pasted multiword names match without rewriting visitor controls or metadata. The exact state filter still combines with the query. Page-return resync runs in a zero-delay timer because persisted form restoration can follow the event; see [the documented history-traversal ordering](https://developer.mozilla.org/en-US/docs/Web/API/Window/popstate_event). Cards, the result count and the empty state then follow restored controls without input events. Unchanged counts do not rewrite the live-region text. The application adds no storage, URL parameters or transmission of search selections.

After submission, the entry checker links a uniquely matched result to its exact stored guidance article. The target follows the selected rule even when two results have identical wording; stale matches retain their historical evidence with an explicit fresh-review label. Results without a unique rule, including conflicts and uncovered dates/areas, link to the general stored-guidance section. This native fragment link stays outside the decision live region, remains hidden before submission and does not automatically move focus or scroll. Existing static evidence and official links remain usable without JavaScript.

Dated-rule and undated-observation articles use `tabindex="-1"` so native evidence links and source-specific correction returns can focus the exact stored article. Tab then continues to its supporting-text disclosure. Direct article fragments also work without JavaScript. These articles stay outside the normal Tab order, and same-page evidence activation preserves trip choices, checklist state, decision wording and source clocks.

Every park checklist offers printing or saving the current page through the browser print dialog. The action prepares freshness/progress before opening it, and native `beforeprint` also updates trip guidance, alerts and history. Printing reconciles silent trip changes but never submits the first entry check or completes a checkbox. The print-only page-copy timestamp is not a source-check/review clock; all source metadata remains unchanged. Park print styles expose wrapped HTTPS destinations and all seven official planning checks with their link-review times. Evidence disclosures retain their open/closed state. Without JavaScript, visitors can use the browser print menu; static print content discloses unrecalculated freshness and an unrecorded copy time. This is a copy of stored guidance and self-reported progress, not a booking or conditions verification. No application storage or transmission is added.

Populated park notice lists offer literal search of their retained titles/descriptions combined with an exact provider category. Category choices come only from that park's current retained records. The shown/total count and no-match message describe the filtered view; feed freshness, unclassified area scope and unconfirmed travel-date applicability remain separate. Controls are hidden until initialized, and the full native source inventory remains usable without JavaScript. Initialization and queued `pageshow` reconciliation read restored controls; unchanged counts do not rewrite the live region. Filters add no application storage, URL parameters or requests.

An exact retained-notice fragment clears conflicting filters and reveals its source article, including on page return. Unknown, malformed and non-notice fragments do not select or replace evidence. Later typing still filters normally with an existing fragment. Print media includes every retained notice with a static disclosure, hides filter controls/counts/empty state and preserves the screen selections and hidden attributes. Filtering, source navigation and printing never rewrite public records or source clocks, and zero matches never establish an all-clear.

The corrections page uses a build-time catalog containing only the validated public dated rules, undated observations and retained notices. Park-page links pass a single public identity, and the browser selects exactly one allowlisted record. Unknown, removed, ambiguous or malformed identities keep the general reporting fallback; query text never supplies wording or draft content. The panel preserves original clocks, review/coverage statuses, nullable notice destinations and provider-link attribution. Rendering uses `textContent`, and native return links target the exact source article under either build base.

GitHub correction drafts use only public identity, source links and metadata, with the canonical hosted park-page URL. Full excerpts, visitor trip choices, unrelated query values and private records are excluded. Drafts use GitHub's documented [issue URL query parameters](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-an-issue#creating-an-issue-from-a-url-query); opening a draft requires the visitor's click and does not submit an issue. Correction-route destinations suppress referrers. General reporting remains usable without JavaScript, with a note to supply the park page and official evidence.

History navigation uses an optional public caller context with the validated paired retained inventory. The changes overview returns to each park's trip-readiness section under either hosting base; matching comparison entries link to a unique same-park retained ID with an explicit stored-evidence disclosure. Park pages use local fragments. Archived before/after wording and removal warnings remain intact, and absent or ambiguous matches imply no reopening. Private previews and archive-only fixture pages supply no public context. See `docs/VISITOR_HISTORY.md`.

Exact same-document notice link activations reveal excluded evidence before native navigation, including when a repeated fragment causes no `hashchange`. Modified activations, other documents and unknown targets keep normal browser handling. Revealed targets accept keyboard focus; already visible targets preserve useful filters. No application storage, URL mutation or source requests are added.

## Clock semantics

`reviewed_at` is our page review, not a publisher change time. `last_checked_at` is an attempted collection. `last_successful_fetch_at` advances only after a complete valid feed. `observed_first_at` and `observed_changed_at` are our observations, not the true start of an event. `source_updated_at` stays null without trustworthy field-specific source evidence. `built_at` is artifact creation; `published_at` stays null without separately established publication metadata. Deploying an existing verified artifact does not rewrite its manifest or source clocks.

The browser recalculates freshness every minute, when the tab becomes visible and on page return. Coverage and history refresh directly on `pageshow` because they read static source metadata; trip controls reconcile in a queued task after restoration. Each source retains its own age, and neither a return nor a code update rewrites evidence clocks. Entry review expiration is 168 hours; alert expiration is four hours. Stale guidance remains readable as historical evidence but cannot grant a current exemption. Trip dates/times are wall-clock values at the park, not UTC conversions from the browser timezone.

Trip decisions replace live-region text only when the displayed title or detail changes. Minute and visibility refreshes still recalculate freshness, including the seven-day expiry transition, without repeatedly rewriting an unchanged result. Trip edits retain the existing checklist reset behavior.

Trip page returns also queue reconciliation after `pageshow`, so restored date, time, area and special-case controls are read after browser restoration. A changed selection clears the previous checklist and refreshes an already submitted decision. Unchanged persisted returns preserve the checks and derive progress from the current checkbox values; a fresh page load clears browser-restored checks, retaining page-only state. Minute/visibility refreshes and submission also detect silent selection changes. Freshness updates on return, while an unsubmitted trip still requires its first explicit check. Unchanged checklist progress does not rewrite its live-region text. No application storage or transmission is added. Synthetic script and browser regressions exercise restoration ordering; they do not establish every browser's restoration policy.

Production verification follows the current paired histories, including later observations and bounded views whose original baseline is no longer visible. Exact metadata, clocks, observation/baseline counts and omission disclosures remain checked. The generated-history regression builds the real component with the isolated archive fixtures and checks both valid views and corrupted output. The generated-site release suite still requires successful public snapshots; accepting degraded synthetic history rendering is not release approval.

`tests/pilot-clock.ts` provides a reference after every known review and attempted/successful feed check. That clock avoids future evidence without making every source fresh. Browser coverage checks preserve each source's independent age; deliberate annual-guidance scenarios use the selected reviews' own clocks and explicit visit dates. Historical/synthetic cases keep independent fixed clocks.

## Collection limits

The collector uses only a fixed NPS HTTPS endpoint. Its private key is in a request header, and redirects are disabled. It permits three attempts with bounded waits, 100 pages and 5,000 total records. Pagination counts must remain stable and IDs unique. A drop of more than half the last-good records is quarantined for review. This conservative threshold intentionally favors retaining notices over implying reopening; a later operator workflow must resolve legitimate mass removals.

The private collector/archive/staging path retains normalized evidence and immutable history receipts, excluding API headers and raw HTTP responses; see `docs/STAGING_COLLECTION.md`. Detailed operator captures, checkpoint metadata and recovery receipts belong in the private handoff outside the website checkout. Public alert updates require deliberate reviewed promotion. Astro escapes notice strings and browser scripts use textContent, not untrusted innerHTML. `parkCode` determines alert scope; a provider URL can be absent, or a validated provider-supplied HTTPS destination. Nullable URLs and safe external links are covered by the tested normalization contract documented in `docs/NPS_PREFLIGHT.md`.

Python collection/archive validation and the public TypeScript validators accept ordinary directory URLs ending in one slash. Validation compares decoded paths without rewriting the stored URL or its normalized-record hash; traversal, repeated separators (including leading `//`) and backslashes remain refused. `tests/notice-url-pipeline.test.ts` runs the actual synthetic staging/archive exporter through snapshot, history, preview and in-memory promotion validation, including unchanged/edited links and failed/quarantined attempts. Its disposable external archive and simulated review envelope do not establish real collection, approval or publication.

The collector also percent-decodes query/fragment text once before its existing credential-like pattern check, matching archive validation. This prevents read-only preflight from reporting `verified` for encoded sensitive inputs that the archive would reject. Default quarantine snapshots preserve accepted evidence and the success clock with a generic review error, advancing only the attempted-check clock; diagnostic mode exposes only the allowlisted reason. Staging retains its existing fallback for other archive-invalid candidates. Synthetic collector/preflight regressions cover the encoded refusal, report sanitization and exact safe URL/hash preservation.

The alert archive and staging APIs share a destination guard before storage operations or requests. It requires an absolute path, rejects raw traversal and symlink ancestry, then checks canonical containment outside the entire checkout and its ancestors. This also rejects Linux doubled-leading-slash checkout aliases and ignored/unlisted checkout folders. Existing private stores are not automatically migrated or repaired; owner-only WSL setup and backup remain deliberate operator responsibilities.

The separate POSIX editorial file guard also checks canonical containment after its raw path and symlink checks. Ledger, capture-input, backup and Python preview callers inherit that boundary, including refusal of doubled-leading-slash checkout/ancestor aliases. Owner-only permissions, single-link regular files and safe error codes retain their existing contracts.

## Release boundaries

Normal PR CI has read-only repository permissions and no source API key. The live pilot uses the manual verified-artifact Pages deployment/rollback workflow; there is no scheduled collection or automatic deployment. CI verifies both domain-root and free GitHub project-path builds. Initial deployment, rollback and restoration were verified at the actual project URL. See `docs/PAGES_RELEASE.md`.

Both generated-site suites run the dependency-free Python helper `tests/site_links.py` from their existing Node test gate. It scans every emitted `.html` file, parses literal `href`/`src` attributes, resolves relative and root-relative destinations, ignores queries for filesystem lookup, and verifies local HTML fragment IDs or named anchors. Encoded names are decoded before checks. Local paths must stay inside the hosting base and output directory. Comments, script/text contents and inert template contents do not supply fragment targets; a `<base>` element is refused because the current builds do not use one.

The checker is offline and requires `python3`, already provided by CI. External URLs are skipped without requests. Its scope excludes `srcset`, CSS URLs, dynamically created links, external availability, and non-HTML fragment semantics. Browser suites remain the check for interactive behavior. `test_site_links.py` exercises the real Node gate against temporary valid and broken outputs under both hosting bases, including pages absent from the fixed content assertions' route list.

The read-only readiness report defaults to the approved ad-free, unindexed pilot. Its JSON schema is version 2, with explicit required gates and separate `indexed`/`advertising` targets. Every target requires durable review, public alert data, backup, source rights, and hosting/rollback evidence. Changed indexing safeguards or detected ads cannot be bypassed by selecting `pilot`. See `docs/RELEASE_READINESS.md`.

Durable review also requires the public guidance inventory to match the private ledger's complete records and their source-specific approval hashes. Each current v2 baseline needs a matching reconciliation that selected that source's holds; carrying imported baselines forward does not prove those sources were reconciled. The report uses the existing canonical digest, compares records by stable ID, and emits only match counts/booleans. A private reconciliation alone does not update or approve different public JSON.

The private entry capture command has an offline `--check-only` mode for path/head/input-availability checks. It shares setup validation with `--live`, including existing owner-only ledger and packet parents, and emits metadata without requests or writes. A successful setup check is not source approval or release readiness. See `docs/PERSISTENT_ENTRY_CAPTURE.md`.

The owner selected a separate private GitHub repository for the remote backup copy. This is an operator transport policy around the unchanged ledger backup/verify/restore tools: retain working data on private WSL storage, upload only verified checkpoints, then freshly download, verify and rehearse recovery. Credentials and public CI artifacts are excluded. A synthetic transport probe does not clear any release gate. See `docs/GITHUB_PRIVATE_BACKUP.md`.

The offline `scripts/prepare-alert-promotion.ts` command reuses strict preview-bundle and history validation to prepare a private Git patch for the five public alert snapshots and their paired history. It binds all six base-file hashes, preserves overlapping observations/cumulative counts, replays new record changes and clocks from the public checkpoint, and refuses rewinds/forks/unverifiable or omitted-change gaps. It preserves degraded states and writes only to owner-only POSIX storage outside the checkout. Preparing the patch is not real public-data promotion or approval; applying it requires a deliberate operator review. See `docs/ALERT_DATA_PROMOTION.md`.

An explicit `--archive-dir` adds a read-only Python check for gaps outside the bounded preview. The existing archive reader replays complete committed chains, then the shared projection helper binds the precise public and candidate prefixes plus bundle identity. Only count/hash metadata crosses the bounded subprocess bridge. Matching archive proof permits omitted visitor observations/changes while retaining their labels; it never exports full chains, changes source clocks or approves source data. No archive lookup occurs by default.

The same command's `--check --bundle PATH --patch PATH --candidate-id HASH` mode regenerates the exact candidate and compares the private patch bytes plus the recorded preparation hash. It shares the original bundle/base/continuity validation, including all six public base hashes and optional archive verification, and refuses missing or changed inputs without writing. Check success is point-in-time consistency, not human approval or an application action. See the operator guide for the exact CLI order and unchanged-input requirement before a separately authorized application.

Upstream `tracker.preview` now enforces the same private bundle storage boundary: an absolute output outside the entire checkout, an existing owner-only parent, owner-only output directory and single-link regular files. It reuses the existing POSIX guards and refuses insecure retained candidates before creating a writer lock, rather than chmod or move existing files. Synthetic browser inputs use caller-owned temporary storage outside the checkout, removed after the isolated preview build has copied its input. See `docs/PREVIEW_BUNDLES.md` for migration from older relative `state/` destinations.

The preview builder also requires an explicit external `--workspace-parent`. Input and workspace permissions are verified, build children use private creation permissions, and readiness checks inspect the complete bounded workspace tree before completion or serving. Astro runs inside that workspace with a separately pinned source root and bundled prerender dependencies, keeping intermediate files outside the checkout across filesystems. The synthetic browser harness removes its external build directory after the server exits. Existing in-checkout preview workspaces must be rebuilt using the updated operator command.

The initial editing environment could not download npm dependencies, so a temporary feature-branch job generated the lockfile without lifecycle scripts and a separate job committed only that lockfile. That bootstrap workflow has been removed. Local development and normal CI now use `npm ci` with the committed lockfile; there is no permanent write-enabled dependency bootstrap.

## Review notes

Self-review reproduced and fixed impossible JavaScript date normalization, acceptance of cross-park notice URLs, incoherent previous attempt/success timestamps and credential-like query parameters. Independent code-review findings and their fixes are recorded in PROJECT_STATUS.md; no field conditions audit is claimed. Run the complete CI suite and inspect its exact commit before approval. Current results and the next coherent task belong in PROJECT_STATUS.md.
