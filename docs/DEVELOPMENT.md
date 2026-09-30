# Development guide

## Structure

`data/parks.json` holds the reviewed pilot inventory, park-specific official URLs and IANA timezones. `data/rules.json` holds annual entry guidance, exact excerpt evidence and rights-review metadata. `data/alerts/*.json` holds collector state, initially never checked.

`src/lib/readiness.ts` is the pure clock-injected decision layer. `scripts/validate-data.ts` gates build-time inventory, hashes, timestamp coherence and source scope. `tracker/alerts.py` handles injectable collection, bounded transport and atomic writes. Astro pages/components render meaningful HTML, and small browser scripts handle search and page-only trip choices. Tests use synthetic provider responses, never live network requests.

## Clock semantics

`reviewed_at` is our page review, not a publisher change time. `last_checked_at` is an attempted collection. `last_successful_fetch_at` advances only after a complete valid feed. `observed_first_at` and `observed_changed_at` are our observations, not the true start of an event. `source_updated_at` stays null without trustworthy field-specific source evidence. `built_at` is artifact creation; `published_at` stays null because no deployment is configured.

The browser recalculates freshness every minute and when the tab becomes visible. Entry review expiration is 168 hours; alert expiration is four hours. Stale guidance remains readable as historical evidence but cannot grant a current exemption. Trip dates/times are wall-clock values at the park, not UTC conversions from the browser timezone.

## Collection limits

The collector uses only a fixed NPS HTTPS endpoint. Its private key is in a request header, and redirects are disabled. It permits three attempts with bounded waits, 100 pages and 5,000 total records. Pagination counts must remain stable and IDs unique. A drop of more than half the last-good records is quarantined for review. This conservative threshold intentionally favors retaining notices over implying reopening; a later operator workflow must resolve legitimate mass removals.

The private collector/archive/staging path now retains raw response evidence and immutable history receipts; see `docs/STAGING_COLLECTION.md`. Public alert snapshots remain `never_checked`, and no real durable capture has been performed here. Astro escapes notice strings and browser scripts use textContent, not untrusted innerHTML. `parkCode` determines alert scope; a provider URL can be absent, or a validated provider-supplied HTTPS destination. Nullable URLs and safe external links are covered by the tested normalization contract documented in `docs/NPS_PREFLIGHT.md`.

## Release boundaries

Normal PR CI has read-only repository permissions and no source API key. A manual verified-artifact Pages deployment/rollback workflow exists; there is no scheduled collection. CI verifies both domain-root and free GitHub project-path builds. No production deployment has been dispatched. See `docs/PAGES_RELEASE.md`.

Both generated-site suites run the dependency-free Python helper `tests/site_links.py` from their existing Node test gate. It scans every emitted `.html` file, parses literal `href`/`src` attributes, resolves relative and root-relative destinations, ignores queries for filesystem lookup, and verifies local HTML fragment IDs or named anchors. Encoded names are decoded before checks. Local paths must stay inside the hosting base and output directory. Comments, script/text contents and inert template contents do not supply fragment targets; a `<base>` element is refused because the current builds do not use one.

The checker is offline and requires `python3`, already provided by CI. External URLs are skipped without requests. Its scope excludes `srcset`, CSS URLs, dynamically created links, external availability, and non-HTML fragment semantics. Browser suites remain the check for interactive behavior. `test_site_links.py` exercises the real Node gate against temporary valid and broken outputs under both hosting bases, including pages absent from the fixed content assertions' route list.

The read-only readiness report defaults to the approved ad-free, unindexed pilot. Its JSON schema is version 2, with explicit required gates and separate `indexed`/`advertising` targets. Every target requires durable review, public alert data, backup, source rights, and hosting/rollback evidence. Changed indexing safeguards or detected ads cannot be bypassed by selecting `pilot`. See `docs/RELEASE_READINESS.md`.

Durable review also requires the public guidance inventory to match the private ledger's complete records and their source-specific approval hashes. Each current v2 baseline needs a matching reconciliation that selected that source's holds; carrying imported baselines forward does not prove those sources were reconciled. The report uses the existing canonical digest, compares records by stable ID, and emits only match counts/booleans. A private reconciliation alone does not update or approve different public JSON.

The private entry capture command has an offline `--check-only` mode for path/head/input-availability checks. It shares setup validation with `--live`, including existing owner-only ledger and packet parents, and emits metadata without requests or writes. A successful setup check is not source approval or release readiness. See `docs/PERSISTENT_ENTRY_CAPTURE.md`.

The initial editing environment could not download npm dependencies, so a temporary feature-branch job generated the lockfile without lifecycle scripts and a separate job committed only that lockfile. That bootstrap workflow has been removed. Local development and normal CI now use `npm ci` with the committed lockfile; there is no permanent write-enabled dependency bootstrap.

## Review notes

Self-review reproduced and fixed impossible JavaScript date normalization, acceptance of cross-park notice URLs, incoherent previous attempt/success timestamps and credential-like query parameters. Independent code-review findings and their fixes are recorded in PROJECT_STATUS.md; no field conditions audit is claimed. Run the complete CI suite and inspect its exact commit before approval. Current results and the next coherent task belong in PROJECT_STATUS.md.
