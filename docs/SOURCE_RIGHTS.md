# Exact public NPS text source-rights evidence

## Scope

This review covers only the six public guidance records currently stored in:

- `data/rules.json`; and
- `data/entry-notes.json`.

Those six records point to five official NPS pages. The project republishes only a short reviewed text excerpt from each record plus original project-authored planning summaries.

This is not a blanket rights conclusion for the full source pages or NPS website.

## Official policy basis

Reviewed September 29, 2026.

NPS ownership/disclaimer:

`https://www.nps.gov/aboutus/disclaimer.htm`

The NPS disclaimer states that material created by the National Park Service and presented on its website is generally considered public domain unless otherwise indicated. It also says commercial republication should include a reference to the original U.S. Government work and gives examples including:

> No protection is claimed in original U.S. Government works.

The same disclaimer warns that not all NPS-site material is public domain and specifically distinguishes protected NPS marks and other material.

NPS Arrowhead permission guidance:

`https://www.nps.gov/subjects/partnerships/arrowhead-requests.htm?fullweb=1`

The Arrowhead is a protected NPS service mark and is outside this project's approved public-content scope.

## Machine-readable evidence

`data/source-rights.json` binds the policy review to every current public guidance record.

For each guidance record it stores:

- guidance ID;
- exact official source URL;
- classification `nps_government_text`;
- allowed use scope `short_text_excerpt_and_original_summary`;
- `third_party_material_reproduced:false`;
- `nps_marks_reproduced:false`; and
- `media_reproduced:false`.

The policy section also records:

- the official NPS ownership/disclaimer URL;
- the official NPS mark-permission URL;
- the required commercial government-work notice;
- third-party material not allowed by this evidence;
- NPS marks not allowed by this evidence; and
- private raw captures not approved for public publication.

## Build enforcement

`scripts/validate-source-rights.ts` is called by the normal data build gate.

A build fails if:

- a public guidance record is missing from the manifest;
- a record is duplicated;
- a guidance ID/source URL pairing changes without a corresponding review;
- the policy source URLs or commercial notice change;
- any covered record claims third-party material;
- any covered record claims NPS marks; or
- any covered record claims media reproduction.

This means a guidance-data change cannot silently retain old rights evidence.

## Public notice

The common site footer includes:

“Source excerpts are attributed to the National Park Service. No protection is claimed in original U.S. Government works.”

The existing statement that the project is independent and not affiliated with or endorsed by the National Park Service remains immediately adjacent.

## Media and marks boundary

The current public `src/` and `public/` trees contain no image/audio/video assets.

The readiness gate also refuses the current text-only rights pass if it detects:

- a public media asset;
- a media tag referencing NPS-hosted content; or
- an apparent NPS Arrowhead/logo/mark media asset.

Explanatory text discussing the fact that NPS marks are excluded is permitted; that is not reproduction of a mark.

## Private raw captures

Private source-review HTML retained in the owner-controlled editorial ledger is not public site content and is **not** covered for public redistribution by this manifest.

The manifest explicitly records `raw_private_captures_public:false`.

## Limits

This is a product evidence record based on the current official NPS policy and the exact current uses. It is not legal advice.

A new review is required before adding or publicly reproducing:

- photographs;
- graphics or maps;
- audio/video;
- the Arrowhead or other NPS marks;
- third-party material appearing on an NPS page;
- full-page/source captures;
- materially longer source text; or
- new source families not covered by the manifest.
