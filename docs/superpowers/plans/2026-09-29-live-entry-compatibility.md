# Live entry-page compatibility plan

> Execute inline with superpowers:executing-plans and test-driven-development.

**Goal:** Verify actual fixed NPS entry pages through the existing extractor and private ledger, repairing evidenced incompatibility without approving guidance.
**Architecture:** Preserve the extractor/review/ledger APIs. Add a bounded, explicitly requested compatibility probe using standard-library HTTPS and temporary owner-only storage. Keep only structural diagnostic metadata public. No raw captures, pending text or baselines are uploaded.
**Tech stack:** Existing Python, Node and GitHub Actions; no new dependencies.
**Spec:** PROJECT_STATUS.md next task and docs/ENTRY_SOURCE_EXTRACTION.md.

## Constraints
No API key, credential lookup, redirects, retry loop, deployment, schedule, approval renewal or production dataset changes. One request per exact configured entry source, 1 MiB maximum each, socket timeout and five-minute diagnostic-job cap. A diagnostic exit/status does not establish source approval, current park conditions or permanent retention. Context baselines remain explicit reviewer inputs.

## Tasks
- [x] Probe raw live HTML, preserving raw-byte digests and retrieval clocks in safe metadata only.
- [x] Reproduce the shared redundant document-closing trailer, plus appended-text false matches, with minimized synthetic markup tests. Repair only this evidenced envelope shape; continue refusing malformed interior markup and unexpected out-of-body content.
- [x] Test a reusable opt-in probe (fixed URLs, bounded response/type checks, safe reports, original check clocks). Run supplied captures through inspect_entry_sources and the original SQLite/TypeScript ledger gate in temporary private storage. Do not create approvals.
- [ ] Rerun the live check and full CI, review diff, retire temporary push invocation, update handoff and PR with exact results and unmet gates.

## Evidence and rulings
Base dc3c794e73a9b9b7842c9c7ec334a7410573b773; main unchanged. GitHub/NPS DNS unavailable in container. A source-only git archive from diagnostic run 36574128149 was downloaded and verified (ZIP SHA256 c942fb0cc8959b7da4944bee245fe2a8ba726e378cdfc36816398138fa7e536a), enabling a full isolated local source snapshot, not a clone with upstream history.

Probe 36574128149 fetched all five exact pages with HTTP 200, 36–111 kB, no prohibited codepoints; all failed ambiguous_html. A second targeted diagnostic, 36574421469, identified a redundant closing body tag after one already closed body and an empty stack, preceded by scripts. No parser guard had been relaxed. Subsequent repair rejects appended prose/elements rather than broadly ignoring everything after the first body.

Ruling: the initial inline workflow was disposable diagnostic instrumentation, not the retained capture API. Temporary push execution requires a specific message marker and exact branch; remove it after verification. The permanent diagnostic is manual only. No source capture artifact is permitted. Baseline Python 3.13 run exposed one pre-existing stderr assertion contaminated by SQLite ResourceWarnings; CI uses Python 3.12. Do not alter unrelated tests to conceal it.

Local RED/GREEN: 14 envelope methods initially produced 9 failed assertions and 4 errors, including genuine silent-discard failures for out-of-body text and elements. All 14 pass after the narrow guard repair; all 30 original extraction tests remain passing. The 14 diagnostic methods were observed failing against explicit unimplemented interfaces, then pass with real extraction/gate/ledger replay. The local entry-family suite passes 100 Python tests and 8 cross-language Node tests. Full CI and live end-to-end capture are pending for this implementation commit.
