# Live entry-page compatibility plan

> Execute inline with superpowers:executing-plans and test-driven-development.

**Goal:** Verify actual fixed NPS entry pages through the existing extractor and private ledger, repairing evidenced incompatibility without approving guidance.
**Architecture:** Preserve extractor/review/ledger APIs. Add a bounded, explicitly requested compatibility probe using standard-library HTTPS and temporary owner-only storage. Keep only diagnostic metadata public. No raw captures, pending text or baselines are uploaded.
**Tech stack:** Existing Python, Node and GitHub Actions; no new dependencies.
**Spec:** PROJECT_STATUS.md next task and docs/ENTRY_SOURCE_EXTRACTION.md.

## Constraints
No API key, credential lookup, redirects, retry loop, deployment, schedule, approval renewal or production dataset changes. One request per exact configured entry source,1MiB maximum each,15-second socket timeout and five-minute diagnostic-job cap. Socket timeout is not an absolute slow-stream/DNS deadline. A successful diagnostic is not source approval, current park conditions or permanent retention. Context baselines remain explicit reviewer inputs.

## Tasks
- [x] Probe raw live HTML, preserving raw-byte digests and retrieval clocks in safe metadata only.
- [x] Reproduce the shared redundant document-closing trailer plus appended-text false matches with minimized synthetic markup tests. Repair only this evidenced envelope shape; continue refusing malformed interior markup and unexpected out-of-body content.
- [x] Test the opt-in probe, fixed URLs, bounded response/type checks, safe reports and original clocks. Run captures through inspect_entry_sources and the original SQLite/TypeScript ledger gate in temporary private storage, without approvals.
- [x] Run actual live capture/replay and full CI, review the diff, prepare the manual-only workflow, update handoff and PR. Verify the final config/documentation commit separately; no merge or deployment.

## Evidence and rulings
Base dc3c794e73a9b9b7842c9c7ec334a7410573b773; main unchanged. GitHub/NPS DNS unavailable in container. A source-only git archive from run36574128149 was downloaded and verified (ZIP SHA256 c942fb0cc8959b7da4944bee245fe2a8ba726e378cdfc36816398138fa7e536a), enabling a complete isolated source snapshot, not a clone with upstream history. Its upload step was removed; no page bodies were uploaded.

Probe36574128149 fetched five exact pages with HTTP200,36–111kB,no prohibited codepoints; all failed ambiguous_html. Targeted diagnostic36574421469 identified the redundant closing body after one closed body and empty stack, preceded by scripts. These were successful diagnostic invocations, not successful compatibility results.

Ruling: allow one exact redundant body/html closing pair only after a complete document. Refuse visible appended/prebody text and elements instead of ignoring everything outside the body. Interior balancing, base URL and annotated/deleted-text guards remain. Non-rendering script/style behavior stays explicitly outside scope.

Ruling: the initial inline workflow was disposable instrumentation. Marker-gated push execution was temporary; the handoff removes it and retains workflow_dispatch only, with no schedule or capture artifacts. The diagnostic uses a temporary private ledger and cannot create approved baselines or a persistent live archive.

Local RED/GREEN:14 envelope methods initially produced9 failed assertions and4 errors, including genuine silent-discard failures. All14 then passed plus30 original extraction tests. Fourteen diagnostic methods first ran against explicit unimplemented interfaces, then passed with real extractor/gate/ledger replay. Local entry-family100Python and8cross-languageNode tests passed; compileall passed. A complete local Python3.13 baseline had a pre-existing SQLite ResourceWarning/stderr failure; complete Node execution lacked installed Astro (136pass/2fail). No full local pass or unrelated test relaxation is claimed.

**Actual live GREEN:** diagnostic#3/run36575873171/job109431220513/head a98487ec123b629ba433deee00fe3ab24b29fc4c. At2026-09-29T13:32:52.880Z–13:32:53.190Z,all5 HTTP200,all5contexts extracted,existing private ledger replay verified,6pending holds,0approved context baselines,no approval/publication/raw upload. All source reasons were context_not_reviewed, not source changes. Temporary captures were discarded after replay. Full metadata in docs/LIVE_ENTRY_COMPATIBILITY.md.

**Full CI GREEN:** Verify pilot#44/run36575877382/job109431236802, same implementation head, temporary PR merge28b113ba5a98d721289208ec39a91191a7521abd. 138Node+258Python+18static+74Chromium=488tests,28added. Astro24files:0errors/0warnings/0hints. Build14pages+build.json. Complete logs read. Artifact11037711139,CI SHA256331de6b67608ae051bec8598f33d344b73ea11916515bd7f71e6e010d68cb05d; not independently downloaded.

Review is author self-review, not independent approval. The final handoff changes documentation and disables temporary push execution; application/tests are unchanged and final CI is checked separately in PR#1. Next is reviewed persistent reference evidence and explicit approved-guidance reconciliation, not another parser/storage system. No keyed API or key-configuration check occurred.
