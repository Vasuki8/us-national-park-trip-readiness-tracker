# Live entry-page compatibility diagnostic

## Verified result, not a source approval

On **September 29, 2026**, the exact five configured NPS entry pages returned HTTP 200 and their actual response HTML passed the scoped extractor. The supplied six guidance excerpts were found uniquely. The captures, extracted context and six resulting holds were written to and replayed from the existing private SQLite ledger, using the existing TypeScript assessment gate.

Evidence: diagnostic **run 36575873171**, job **109431220513**, commit **a98487ec123b629ba433deee00fe3ab24b29fc4c**.
https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36575873171

All five source results were `context_not_reviewed`, not `matching_reviewed_context`. Output reported `all_contexts_extracted:true`, `ledger_replay_verified:true`, `pending_proposals:6`, `approved_context_baselines:0`, `approval_performed:false`, `publication_performed:false`, and `capture_retention:temporary_diagnostic_only`.

The six holds reflect missing separately reviewed context baselines, **not six confirmed changes to park rules**. No original guidance or review date was refreshed. No real context baseline, public proposal, current alert or history was committed. The temporary diagnostic ledger was removed after successful replay; this run does not create a durable live archive or a retrievable approved capture. The following safe metadata identifies what was tested, but hashes cannot reconstruct source text or authenticate its approval.

## Actual retrieval evidence

All times below are UTC on 2026-09-29 (approximately 9:32 a.m. America/Toronto). Sources are the exact fixed URLs in `tracker/entry_sources.py:PROFILES`; no redirects were followed.

| Park | Started | Capture completed | HTTP | Response bytes |
|---|---|---|---:|---:|
| Yosemite | 13:32:52.677Z | 13:32:52.880Z | 200 | 36,204 |
| Rocky Mountain | 13:32:52.881Z | 13:32:52.946Z | 200 | 110,697 |
| Yellowstone | 13:32:52.946Z | 13:32:53.042Z | 200 | 49,681 |
| Zion | 13:32:53.043Z | 13:32:53.103Z | 200 | 70,977 |
| Grand Canyon | 13:32:53.104Z | 13:32:53.190Z | 200 | 75,580 |

Raw-response SHA-256 and normalized-context SHA-256 respectively:

- yose: `7dee4f4ae054fab86a4165c910301bdda3b6ab735ff1b47325ff14bf8839e721`; `2bcd2185d806ae0cbcea1368a59af3ca41a0936211ac846edbb134b834df89de`.
- romo: `4f433c53d9c500c91955124c3221ce953c452cfa1573a304a893f961117e4ac6`; `63e74ab52eef5189ba6b71a8bbc2d653d131036d6baf7b93ea5865be828ae4a7`.
- yell: `f4b7efbda2bc00377af433b897641ac655e9f28f0cd8e68883d1ce022f698358`; `8fd2626af533f26f338e20ea2e836a3679e96991913bc102f68c6c32f8cca1cd`.
- zion: `857697eede1b491ccb3048d15bd490d2bbdc929a8d2bc3fc7631d9f15d110626`; `b1f7af0c44f01dac6229aba57c7dcd06869500611394e7b9732a12dc47c8cd0c`.
- grca: `460da7987b119abe21203cc1279537976edfa36c168eb403952e9dd484bb20a5`; `6840c78825d16276f6794469f373c03cb7f0bd2b626ea321e0695b185218eb47`.

## Reproduced incompatibility and repair

Initial diagnostic run 36574128149 fetched all five pages successfully but all failed `ambiguous_html`. Targeted run 36574421469 confirmed the same structure: a second closing body tag after an already completed document, preceded by script tags. These earlier successful workflow executions were **not** successful compatibility results.

The parser now allows one exact redundant body/html closing pair after a complete document. Script/style content remains outside the non-rendering comparison scope. This is not generalized HTML error repair: missing or misnested interior tags, duplicate opening bodies, partial/reordered closing pairs and inserted visible elements still refuse.

The new tests also reproduced a separate false-match problem: visible text before or after the body could previously be silently discarded. Such out-of-body text or new visible elements now require review. Base URL and struck-out-text guards remain in force. Minimized synthetic markup tests retain the observed structural case without redistributing real page bodies.

## Operator command

With the repository's supported Python/uv and Node versions installed:

```sh
uv run --frozen python -m tracker.entry_compatibility --live
```

Without exactly `--live`, the CLI refuses before source requests. It issues one HTTPS GET per fixed source, without keys, cookies, redirects or retries. It validates HTTP status, content type/encoding, response length, UTF-8 decoding, source identity and original clocks. Maximum response size is 1 MiB per source. Arbitrary URLs and malformed receipt substitutions are rejected.

The socket timeout is 15 seconds per blocking operation; it is not a complete DNS or slow-stream wall-clock deadline. The retained GitHub diagnostic separately limits the entire job to five minutes. Its final workflow is **manual dispatch only**, read-only repository permission, no secret injection and no capture artifact upload. Registration/availability of manual workflow invocation on the default branch is not claimed while this PR remains unmerged. Temporary marker-gated push invocation used for development has been removed.

The command uses a temporary owner-only directory outside the repository and the existing ledger for end-to-end verification. It returns metadata only; it does not offer a persistent capture export. Exit zero means the batch was extracted and replayed, not that source context was approved. Failures do not overwrite public data. The separate NPS alert API key/preflight is unrelated to these public HTML requests and remains unverified.

## Remaining boundaries

The accepted scope is body text, block boundaries, H1 text and anchor targets. Script/style behavior, media, embedded documents, linked pages and dynamically loaded content remain outside it. HTTP success plus extraction is not a guarantee of current access, a complete rendered-page comparison, or indefinite compatibility with future NPS markup.

Private baseline review, explicit approved-guidance reconciliation, persistent evidence retention, content-use review and publication approval remain separate requirements. Do not manufacture context approvals from hashes or from the presence of a saved sentence. Do not clear existing holds when starting another diagnostic. Since existing ledgers replay through the current parser, a newly rejected old input requires explicit operator investigation; do not rewrite its original event or bypass verification.

No deployment, collection schedule, indexing, advertising or source agreement was enabled. No raw live capture was uploaded. Review is author self-review, not independent certification.

Implementation references: Python HTTPSConnection behavior https://docs.python.org/3.12/library/http.client.html; tokenizer limitations https://docs.python.org/3.12/library/html.parser.html. These references do not establish full browser/HTML-standard compatibility.
