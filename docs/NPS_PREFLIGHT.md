# Read-only NPS preflight

Run `uv run --frozen python -m tracker.preflight` with `NPS_API_KEY` supplied privately, or use the dedicated GitHub workflow. Do not put the key in command arguments, URLs, files committed to Git, or chat.

The workflow uses a repository Actions secret named `NPS_API_KEY`. Its initial trigger is limited to changes to `.github/workflows/nps-preflight.yml` on `feat/pilot-foundation`; it is not a recurring schedule. It has read-only repository permissions, no persisted checkout credentials, and no deployment step. A manual-dispatch trigger is also defined, but GitHub's Run workflow control generally requires the workflow on the default branch. While this PR is draft, an existing preflight run can be rerun after configuring the secret.

The diagnostic checks only the five pilot parks, with at most two requested pages per park. The existing transport bounds each page to three HTTP attempts. Provider redirects remain disabled. The report contains status, counts, attempted-at timestamps and page counts, never API keys, exception text, notice bodies or raw payloads. No site data or snapshots are written. This intentionally does not retain a real-response fixture yet.

`status: not_configured` and `gate_passed: false` mean the runner did not receive a nonempty key. They do not distinguish absent, restricted, environment-only or incorrectly named secrets. No HTTP requests are made in that case. A green diagnostic job by itself does not verify the integration; consumers must require `gate_passed: true`.

`status: verified` means all checked responses normalized successfully within the budget. It does not establish complete conditions coverage, independently validate a park's operating state, or activate scheduled collection. `needs_review` indicates at least one failed/quarantined/budget-limited response. Do not publish those responses automatically.

## Latest observed rerun

Run **36481482091**, job **109224608968**, at **2026-09-29T02:13:16Z**:

```json
{"schema_version":1,"mode":"read_only","status":"not_configured","gate_passed":false,"publication_performed":false,"checks":[]}
```

The runner again received an empty `NPS_API_KEY`. No provider request, site-data change or publication occurred. The diagnostic completed successfully, but the live integration gate remains blocked. This describes the key supplied to this particular workflow execution, not a direct inspection of repository secrets.

This rerun used the original preflight checkout **0dce38beb7c1d9bc3d7feba0d8a69ca1f97ddca7**, not the current application branch head. A rerun does not automatically validate newer application code. Before live validation after relevant code changes, make sure the executed revision is the intended reviewed revision.

Latest job: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36481482091/job/109224608968

## First observed run

The first execution of run 36481482091, job 109127917904, at 2026-09-28T20:45:52Z returned the same empty-key/no-request diagnostic. It is retained here as historical evidence, not reused as the latest configuration check.

Run: https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36481482091

## Owner setup and next validation

Add `NPS_API_KEY` under repository Settings → Secrets and variables → Actions → Secrets → New repository secret, then rerun the existing read-only preflight. Request a personal key through https://www.nps.gov/subjects/developer/get-started.htm. GitHub secret handling: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets. Do not send the key through chat or an issue.

After an owner-controlled key is available, repeat the preflight, inspect actual record shapes privately and retain a reviewed credential-free fixture. The collector, private evidence archive, staging/recovery and isolated preview implementations already exist: use those paths rather than rebuilding them. Operator-controlled persistent storage is still required before scheduling; ephemeral Actions checkouts are not a durable private archive. Source-content approval, production hosting/publication, advertising and indexing remain separate requirements.
