# Read-only NPS preflight

Run `uv run --frozen python -m tracker.preflight` with `NPS_API_KEY` supplied privately, or use the dedicated GitHub workflow. Do not put the key in command arguments, URLs, files committed to Git, or chat.

The workflow uses a repository Actions secret named `NPS_API_KEY`. It runs on `feat/pilot-foundation` when the preflight workflow, `tracker/preflight.py`, or `tracker/alerts.py` changes; this is a validation trigger, not a recurring schedule. It has read-only repository permissions, no persisted checkout credentials, and no deployment step. A manual-dispatch trigger is also defined, but GitHub's Run workflow control generally requires the workflow on the default branch.

The diagnostic checks only the five pilot parks, with at most two requested pages per park. The existing transport bounds each page to three HTTP attempts. Provider redirects remain disabled. The report contains status, counts, attempted-at timestamps and page counts, never API keys, exception text, notice bodies or raw payloads. No site data or snapshots are written. This intentionally does not retain a real-response fixture yet.

`status: not_configured` and `gate_passed: false` mean the runner did not receive a nonempty key. They do not distinguish absent, restricted, environment-only or incorrectly named secrets. No HTTP requests are made in that case. The CLI now returns exit **2**, so the Actions job is visibly failed rather than green while the integration gate is blocked.

`status: verified` means all checked responses normalized successfully within the budget and is the only state that returns exit **0**. It does not establish complete conditions coverage, independently validate a park's operating state, or activate scheduled collection. `needs_review` returns exit **1**. `not_configured` and `invalid_configuration` return exit **2**. Do not publish these diagnostic responses automatically.

## Latest current-revision run

Run **36607959537**, job **109541744290**, head **16dda2f20c504ada6d9740c1de38f458e47cb7f9**, at **2026-09-29T17:52:04Z**:

```json
{"schema_version":1,"mode":"read_only","status":"not_configured","gate_passed":false,"publication_performed":false,"checks":[]}
```

The current feature-branch runner still received an empty `NPS_API_KEY`. It made **zero NPS provider requests**, wrote no snapshots, and performed no publication. The diagnostic step exited **2**, so the workflow conclusion is intentionally **failure** while this release gate is unconfigured.

This is stronger evidence than the earlier rerun because it executed the current preflight/collector revision rather than the original September 28 checkout. It still does not reveal whether the repository secret is absent, incorrectly named, restricted, or otherwise unavailable to this workflow; GitHub does not expose the secret value here.

Run: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36607959537  
Job: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36607959537/job/109541744290

## Historical September 28 rerun

Run **36481482091**, job **109224608968**, at **2026-09-29T02:13:16Z** returned the same `not_configured` / no-request result, but its checkout was the older **0dce38beb7c1d9bc3d7feba0d8a69ca1f97ddca7** and its job conclusion was green under the former diagnostic-completion exit semantics. It remains historical evidence only.

## First observed run

The first execution of run 36481482091, job 109127917904, at 2026-09-28T20:45:52Z returned the same empty-key/no-request diagnostic. It is retained here as historical evidence, not reused as the latest configuration check.

Run: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36481482091

## Owner setup and next validation

Add `NPS_API_KEY` under repository Settings → Secrets and variables → Actions → Secrets → New repository secret, then rerun the existing read-only preflight. Request a personal key through https://www.nps.gov/subjects/developer/get-started.htm. GitHub secret handling: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets. Do not send the key through chat or an issue.

After an owner-controlled key is available, repeat the preflight, inspect actual record shapes privately and retain a reviewed credential-free fixture. The collector, private evidence archive, staging/recovery and isolated preview implementations already exist: use those paths rather than rebuilding them. Operator-controlled persistent storage is still required before scheduling; ephemeral Actions checkouts are not a durable private archive. Source-content approval, production hosting/publication, advertising and indexing remain separate requirements.
