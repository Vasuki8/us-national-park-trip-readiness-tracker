# Pilot release-readiness report

## Purpose

`tracker.release_readiness` is a conservative, read-only summary of the five-park pilot's remaining launch gates.

It does not decide that the product should launch. It reports what the repository and explicitly supplied private evidence can actually prove.

Missing evidence is never a pass.

## Commands

Repository-only human-readable report:

```sh
uv run --frozen python -m tracker.release_readiness --format text
```

Repository-only JSON report:

```sh
uv run --frozen python -m tracker.release_readiness --format json
```

After an owner-controlled private ledger and verified backup exist:

```sh
uv run --frozen python -m tracker.release_readiness \
  --format text \
  --store /absolute/private/entry-review \
  --backup /absolute/private/backups/BACKUP_ID
```

`--backup` is refused unless `--store` is also supplied. The backup is replay-verified by the existing backup module before its manifest can affect the report.

The CLI prints no supplied private path.

Exit codes:

- `0`: every gate is `pass`;
- `1`: a normal report was produced but at least one gate is `blocked` or `not_checked`;
- `2`: arguments/evidence could not be safely evaluated.

## Gate statuses

Every gate has one of exactly three statuses:

- `pass` — the evidence required by this evaluator is present;
- `blocked` — available evidence explicitly shows the gate is not ready;
- `not_checked` — the needed evidence is absent or requires external validation.

Both `blocked` and `not_checked` block `release_ready`.

## Gates

### Durable source review

Without a private ledger: `not_checked`.

With a verified private ledger, this gate passes only when:

- all five fixed source URLs have schema-v2 context baselines created by explicit reconciliation; and
- the current proposal register is empty.

Legacy schema-v1 baselines do not satisfy this release gate.

### NPS alert API

The report reads the five public alert snapshots in `data/alerts/`.

Any `never_checked` snapshot blocks the gate. An empty record list is never interpreted as “no alerts.”

Even if all five snapshots later show successful collection, the static report remains `not_checked` until release-time freshness/provider compatibility is separately established. Collection success alone is intentionally not a self-certifying launch signal.

### Private storage backup

Without a supplied private ledger: `not_checked`.

With a ledger but no verified backup: `blocked`.

A verified backup passes only when its manifest matches the exact current ledger revision and event count. A valid but older backup is blocked as stale for release purposes.

### Source-rights review

The report requires both the record-level `rights_basis` / `rights_reviewed_at` fields and the exact-scope `data/source-rights.json` manifest.

The gate passes only when:

- all six current public guidance records have rights metadata;
- the manifest exactly matches all six guidance IDs and official source URLs;
- every use remains `nps_government_text` limited to a short text excerpt plus original summary;
- no third-party material, NPS marks, or media are claimed as reproduced;
- the required commercial U.S. Government-work notice is present in the public footer; and
- no public media asset or NPS-hosted/mark media use is detected in the current application.

The manifest is grounded in the official NPS disclaimer and Arrowhead-use guidance. This pass applies only to the current six public text uses. It is not blanket clearance for NPS media, marks, third-party material, private raw captures, or future content.

### Hosting and rollback

A manual GitHub Pages deployment/rollback workflow is now present, so this gate is `not_checked` rather than `blocked`.

The workflow can only reuse a successful default-branch `Verify pilot` artifact whose run ID and exact commit SHA are explicitly supplied. It has not been dispatched, so no live production URL or rollback behavior has been verified.

The current build uses root-absolute URLs. The release workflow refuses a nonempty GitHub Pages `base_path`, preventing deployment to the default project-page subpath where those URLs would break. Root-hosting/custom-domain configuration or a future base-path-aware build is still required before a real deployment can succeed.

The evaluator never deploys.

### Search indexing

The evaluator checks three independent repository controls:

- the page `meta robots` directive;
- `public/robots.txt`; and
- the `X-Robots-Tag` response header.

If any still disables indexing, the gate is `blocked`.

If all are removed, the gate becomes `not_checked` until actual crawlability/indexability is verified. The evaluator never changes these controls.

### Advertising readiness

If no known advertising integration markers are present in `src/` or `public/`, the gate is `blocked`.

If ad integration is later present, the gate becomes `not_checked` until policy/consent/readiness review is separately established.

The evaluator never enables ads or analytics.

## Current repository result

As of the verified implementation head on September 29, 2026:

- **1 pass**
- **3 blocked**
- **3 not checked**
- **release_ready: false**

The three explicit blockers are:

1. all five alert snapshots are `never_checked`;
2. indexing is still disabled; and
3. advertising is not enabled.

The three not-checked gates are:

1. durable source review, because no owner private ledger was supplied here;
2. storage backup, for the same reason; and
3. hosting/rollback, because the manual verified-artifact workflow exists but no real deployment or rollback has been exercised.

The current source-rights gate is the one passing gate, limited to the exact six public NPS text uses documented in `data/source-rights.json`.

## Safety properties

The report:

- performs no network access;
- writes no files;
- does not mutate the private ledger or backup;
- does not deploy;
- does not change indexing;
- does not enable ads;
- does not call source capture or reconciliation;
- does not turn absent evidence into success; and
- does not claim that an empty alert list is an all-clear.

It is a release evidence dashboard, not a release action.
