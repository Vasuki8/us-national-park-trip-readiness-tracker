# First real activity source review

Operator collection and offline recovery verified October 4, 2026. This document
records metadata and engineering implications; exact retained source material,
record identities, repository identity and operator receipts remain private.
See the current [handoff](../PROJECT_STATUS.md) for integration status.

## Collected evidence

The first real immutable checkpoint contains 136 individual listings: Yosemite
13, Rocky Mountain 12, Yellowstone 88, Zion 20 and Grand Canyon 3. All five
collections succeeded with `checked_activity_feed_only` coverage. The original
attempt/success clock is `2026-10-04T05:49:46.709637Z`. A successful feed request
does not establish activity availability, exhaustive park coverage or permit
requirements.

The existing private collection, checkpoint verifier, unapproved review export
and restore tools were used. The selected checkpoint was verified before copying,
on the private transfer copy, after a fresh authenticated GitHub clone at the
recorded remote commit and after restoration into a new private destination.
Identity and canonical bytes match; the working evidence is unchanged. See
[GITHUB_PRIVATE_BACKUP.md](GITHUB_PRIVATE_BACKUP.md) for the supported inventory.
This is checkpoint-only recovery, not recovery of an approved activity bundle.

## Review scope and findings

Programmatic inspection scanned all 5,124 retained string values and selected
flagged contexts. It did not establish exhaustive human reading or completed
rights decisions. Every listing supplies an empty credit value; 287 fields
contain HTML. Empty credits do not establish government authorship. No image or
active media tags were found in this scan; that does not resolve text-use rights.

The private report identifies 11 records requiring attention. Observed concerns
include attributed film-producer quotations and production credits; partner,
concessioner and program references; wrapped links carrying identifiable contact
and opaque tracking metadata; HTML style/meta fragments; a listed closure; and
a program whose stated end date preceded collection. Partner references alone
do not prove third-party ownership. Retrieval freshness cannot establish that a
dated program is running or override a stated closure.

A complete private HTML review packet retains all 136 records and 5,032 field
values as escaped literal JSON. Source markup and URLs are not activated. It is
served only on loopback at a private review path, with no directory listing,
external assets or source navigation. Desktop/mobile layout and native
record expansion/keyboard collapse were checked. This packet and its inspection
report remain outside the checkout, builds, backup inventory and public CI.

The [NPS API guide](https://www.nps.gov/subjects/developer/guides.htm) directs
users to the [NPS disclaimer](https://www.nps.gov/aboutus/disclaimer.htm) for
terms of use. NPS government-created work is generally public domain, while
third-party content and protected marks require separate consideration. The
disclaimer does not guarantee complete rights metadata. These official sources
were checked October 4, 2026; no blanket reuse classification was recorded.

## Consequence for development

The current [promotion contract](ACTIVITY_PROMOTION.md) projects every normalized
field and requires exact per-record government-text review across all projected
strings. The observed quotations and link metadata prevent confidently applying
that classification to the complete retained batch. No rights manifest, approval
bundle or public pair was created, and no deployment occurred.

Next design and verify a separately reviewed public projection that keeps the
original evidence private, withholds unresolved text/link content and represents
unknown or conflicting availability honestly. The existing complete projection
has no field-omission mode: changing the public scope requires explicit contract,
review-binding and validation changes before promotion. Technical source handling
does not settle material legal-risk or source-use decisions reserved to the owner.
