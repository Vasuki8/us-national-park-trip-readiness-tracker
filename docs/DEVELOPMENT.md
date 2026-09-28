# Development guide

## Structure

`data/parks.json` holds the reviewed pilot inventory, park-specific official URLs and IANA timezones. `data/rules.json` holds annual entry guidance, exact excerpt evidence and rights-review metadata. `data/alerts/*.json` holds collector state, initially never checked.

`src/lib/readiness.ts` is the pure clock-injected decision layer. `scripts/validate-data.ts` gates build-time inventory, hashes, timestamp coherence and source scope. `tracker/alerts.py` handles injectable collection, bounded transport and atomic writes. Astro pages/components render meaningful HTML, and small browser scripts handle search and page-only trip choices. Tests use synthetic provider responses, never live network requests.

## Clock semantics

`reviewed_at` is our page review, not a publisher change time. `last_checked_at` is an attempted collection. `last_successful_fetch_at` advances only after a complete valid feed. `observed_first_at` and `observed_changed_at` are our observations, not the true start of an event. `source_updated_at` stays null without trustworthy field-specific source evidence. `built_at` is artifact creation; `published_at` stays null because no deployment is configured.

The browser recalculates freshness every minute and when the tab becomes visible. Entry review expiration is 168 hours; alert expiration is four hours. Stale guidance remains readable as historical evidence but cannot grant a current exemption. Trip dates/times are wall-clock values at the park, not UTC conversions from the browser timezone.

## Collection limits

The collector uses only a fixed NPS HTTPS endpoint. Its private key is in a request header, and redirects are disabled. It permits three attempts with bounded waits, 100 pages and 5,000 total records. Pagination counts must remain stable and IDs unique. A drop of more than half the last-good records is quarantined for review. This conservative threshold intentionally favors retaining notices over implying reopening; a later operator workflow must resolve legitimate mass removals.

Notice evidence currently consists of normalized text and an integrity hash. Raw-response archival and complete historical change publication are not implemented. Do not claim audit-complete history. Astro escapes notice strings and browser scripts use textContent, not untrusted innerHTML. Source URLs must belong to the requested park. Legitimate cross-park/empty provider URLs require a reviewed handling rule before acceptance.

## Release boundaries

Normal PR CI has read-only repository permissions and no source API key. There is no deployment or scheduled collection workflow. Hosting, complete source review, production publisher/privacy details, source rights, canonical domain, operator reporting and rollback remain gates before public indexing.

The editing environment cannot download npm dependencies. The one-time feature-branch lock generator ran without lifecycle scripts; a separate job without source checkout committed only the generated lockfile. It checked the exact repository, branch and unchanged head. Its workflow is removed once the lockfile exists. Normal builds use npm ci; there is no permanent write-enabled dependency bootstrap.

## Review notes

Self-review reproduced and fixed impossible JavaScript date normalization, acceptance of cross-park notice URLs, incoherent previous attempt/success timestamps and credential-like query parameters. No independent reviewer or field conditions audit is claimed. Run the complete CI suite and inspect its exact commit before approval. Current results and the next coherent task belong in PROJECT_STATUS.md.
