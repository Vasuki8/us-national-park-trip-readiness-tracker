# Read-only NPS preflight

Run `uv run --frozen python -m tracker.preflight` with `NPS_API_KEY` supplied privately, or use the dedicated GitHub workflow. Do not put the key in command arguments, URLs, files committed to Git, or chat.

The workflow uses a repository Actions secret named `NPS_API_KEY`. It supports manual runs on `main` and retains the existing `feat/pilot-foundation` push trigger for changes to the preflight workflow, `tracker/preflight.py`, or `tracker/alerts.py`. This is a validation trigger, not a recurring schedule. It has read-only repository permissions, no persisted checkout credentials, and no deployment step.

After this workflow change is merged into `main`, open GitHub **Actions → Read-only NPS preflight → Run workflow**, select `main`, and run it. A successful run checks API compatibility for all five pilot parks; it does not collect durable evidence, update public alert snapshots, or deploy the website. The repository Actions secret is used by GitHub Actions and is not automatically available in a local or cloud development shell.

The diagnostic checks only the five pilot parks, with at most two requested pages per park. The existing transport bounds each page to three HTTP attempts. Provider redirects remain disabled. The report contains status, counts, attempted-at timestamps and page counts, never API keys, exception text, notice bodies or raw payloads. No site data or snapshots are written. This intentionally does not retain a real-response fixture yet.

`status: not_configured` and `gate_passed: false` mean the runner did not receive a nonempty key. They do not distinguish absent, restricted, environment-only or incorrectly named secrets. No HTTP requests are made in that case. The CLI now returns exit **2**, so the Actions job is visibly failed rather than green while the integration gate is blocked.

`status: verified` means all checked responses normalized successfully within the budget and is the only state that returns exit **0**. It does not establish complete conditions coverage, independently validate a park's operating state, or activate scheduled collection. `needs_review` returns exit **1**. `not_configured` and `invalid_configuration` return exit **2**. Do not publish these diagnostic responses automatically.

## Current launch evidence

The owner-approved public pilot now contains five successful alert baselines and 17 retained notices. A fresh private read-only preflight at **2026-10-01T02:32:53–55Z** passed all five parks with counts 1/0/5/7/4. It did not refresh the promoted observations, whose original clock remains **2026-10-01T00:20:43.666438Z**. No recurring collection was enabled. Use the existing private collection/review/backup and promotion tools for later updates; credentials and retained source captures remain outside the checkout.

## First verified keyed run (historical)

Run **36628434444**, job **109611267322**, collector head **5cdfee176bdb0d6fc0223962a96b00892bb46ac5**, at **2026-09-29T20:44:13–20:44:14Z** completed successfully:

```json
{
  "schema_version": 1,
  "mode": "read_only",
  "status": "verified",
  "gate_passed": true,
  "publication_performed": false,
  "checks": [
    {"park_code":"yose","collection_status":"success","record_count":1,"pages_requested":1,"diagnostic_code":null},
    {"park_code":"romo","collection_status":"success","record_count":0,"pages_requested":1,"diagnostic_code":null},
    {"park_code":"yell","collection_status":"success","record_count":5,"pages_requested":1,"diagnostic_code":null},
    {"park_code":"zion","collection_status":"success","record_count":8,"pages_requested":1,"diagnostic_code":null},
    {"park_code":"grca","collection_status":"success","record_count":3,"pages_requested":1,"diagnostic_code":null}
  ]
}
```

The repository secret is now available to the workflow and the keyed provider integration is validated for all five pilot parks. The API key itself was never printed or stored in repository data.

The live responses exposed two assumptions in the original collector that were stricter than the official NPS alert schema:

- the alert `url` may be absent; and
- provider-supplied alert links may be external HTTPS links rather than park-path `nps.gov` URLs.

The collector now treats `parkCode` as the authoritative park-scope field, stores a missing alert link as `null`, and accepts provider-supplied HTTPS links after safety validation. It still rejects credentials, secret-like query/fragment values, malformed/path-traversal URLs, localhost/numeric-IP targets, and NPS-lookalike hostnames. External links are labeled in the UI as **“More information link supplied by NPS”** rather than represented as NPS-owned content.

The Python collector/archive guards also accept a single terminal slash in a directory URL, matching the public TypeScript validators. The original accepted URL and normalized-record hash are retained, including safe query/fragment and encoded path text. Decoded traversal, repeated separators and backslashes remain refused. This compatibility repair is verified with synthetic evidence through staging, immutable archive replay and preview/promotion validation; it does not represent a new keyed provider run or refresh public observations.

The collector checks query/fragment text after one percent-decoding pass for the existing credential-like patterns. Encoded `token`, `api_key` or `secret` text now quarantines before normalization reports success; diagnostic preflight reports `needs_review` with `source_query_sensitive` instead of a false `verified` result. The ordinary snapshot retains its generic review error and last accepted records/success clock. Safe encoded URLs retain their original text and hashes. Staging's existing archive-validation fallback already quarantined these inputs and remains unchanged. These cases use synthetic transport only; they do not establish a new provider check.

That successful diagnostic was read-only. It **did not write `data/alerts/`, public history, or publication state**. At that time the public snapshots remained `never_checked`; the later deliberate owner-approved promotion described above is a separate operation.

Run: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36628434444  
Job: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36628434444/job/109611267322

## Diagnostic progression

After the owner added `NPS_API_KEY`, the first keyed run reached the provider but quarantined three parks under the older validator. Safe allowlisted diagnostic codes isolated the causes without exposing alert bodies or credentials:

- Yosemite and Zion: provider-supplied links were outside the old hardcoded NPS-host/path rule;
- Grand Canyon: at least one live alert had no direct URL.

The official NPS alert schema documents the alert URL as a link supplied **“if available.”** The compatibility fixes were developed against synthetic regression tests and repeatedly rechecked against the read-only live preflight until all five parks normalized successfully.

Earlier empty-key and intermediate quarantine runs remain historical diagnostics only; none published data.

## Owner setup and next validation

The repository Actions secret named exactly `NPS_API_KEY` is now functioning and the five-park read-only preflight has passed.

Later alert-data updates require owner-controlled durable collection into the existing private staging/archive path, followed by review before any public snapshot/history update. Do not publish directly from the preflight and do not treat an empty successful feed as an all-clear.

The collector, private evidence archive, staging/recovery, isolated preview and history implementations already exist: reuse those paths. Persistent private storage, source approval, backup recovery and the first public pilot launch have been verified. Scheduling, advertising and indexing remain separate operator decisions.
