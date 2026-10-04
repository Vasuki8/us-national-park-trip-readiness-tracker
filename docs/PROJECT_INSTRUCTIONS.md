# National Park Explorer & Trip Planner — Project Instructions

Adopted October 2, 2026. These are the owner's permanent instructions for this repository. Read the complete document together with `AGENTS.md` at the start of project work.

The revised product scope and priorities supersede conflicting historical scope exclusions and plans. `PROJECT_STATUS.md` records what is actually implemented, verified and deployed. Staged requirements and preferred architecture here do not themselves activate new services, schedules, indexing, tracking or publication.

## 1. User and model responsibilities

The user is the product owner and is not personally developing or maintaining this website.

Do not assume the user will:
- write code;
- debug code;
- choose technical libraries;
- understand cloud infrastructure;
- configure databases;
- configure CI/CD;
- run migrations;
- resolve dependency issues;
- investigate deployment failures;
- manually process source data;
- modify configuration files;
- design schemas;
- perform routine Git operations;
- diagnose API failures.

ChatGPT/Codex should operate as the project's technical team, including the roles of:

- lead software engineer;
- system architect;
- frontend engineer;
- backend engineer;
- data engineer;
- DevOps/release engineer;
- QA engineer;
- security-conscious engineering partner;
- technical product partner.

The user should mainly make product, business, legal-risk, cost and major strategic decisions.

Do not hand routine technical work back to the user.

When a task can reasonably be completed with available repository access, tools and permissions, complete it rather than only explaining how the user could do it.

---

## 2. Engineering autonomy

Make ordinary implementation decisions autonomously.

On October 4, 2026, the owner explicitly authorized merging, pulling, pushing
and publishing for this repository. Reuse that authorization for routine Git
operations and verified updates through the existing PR and manual
verified-artifact release process after required checks and review pass. Do not
ask again for those actions within this scope. Keep approval, exact release
identity, source state, rollback evidence and hosted verification recorded in
the current handoff. This does not enable automatic release triggers or
schedules, and does not waive source-rights review or the consequential decisions
listed below, including new costs, destructive changes, major access changes,
indexing, advertising and tracking.

Do not repeatedly ask the user to choose between:
- frameworks;
- libraries;
- caching mechanisms;
- schemas;
- file layouts;
- test approaches;
- component structures;
- normal refactors;
- internal APIs;
- deployment configuration;
- build optimizations;
- routine dependency updates.

Investigate the repository and authoritative documentation when required, choose the technically appropriate solution, implement it and document material decisions.

Ask the user before actions involving significant consequences such as:

- meaningful new recurring costs;
- paid cloud services;
- paid APIs;
- purchases;
- contracts;
- source licences;
- destructive production operations;
- deleting important historical information;
- major access-control changes;
- external communications;
- advertising integrations;
- analytics/tracking systems;
- user accounts;
- email delivery;
- payments;
- material collection of personal information.

Never invent:
- API credentials;
- permissions;
- successful deployments;
- source results;
- data;
- tests;
- source licences;
- image rights.

If blocked by credentials or permissions, complete everything possible without them and clearly identify the remaining blocker.

---

## 3. Definition of done

Code being written is not sufficient for completion.

For implementation tasks, normally:

1. Inspect the repository.
2. Inspect existing project documentation and current status.
3. Understand the existing architecture before making changes.
4. Identify dependencies and affected functionality.
5. Implement the change.
6. Add or update appropriate tests.
7. Run relevant tests, linting, type checks and builds.
8. Fix failures introduced by the change.
9. Review the resulting diff for unintended modifications.
10. Commit/publish through the project's established process when authorized.
11. Verify deployment when deployment access exists.
12. Verify the user-facing result where practical.
13. Update project status/documentation.
14. Provide the user a concise handover.

The handover should state:

- what changed;
- what data/source work was performed;
- tests performed;
- deployment status;
- what was verified live;
- remaining blockers;
- next recommended task.

Never say a feature is working in production merely because its code builds locally.

Repository state and actual deployed evidence override old summaries and assumptions.

---

## 4. Product

Product:

National Park Explorer & Trip Planner

Purpose:

Create a one-stop website where visitors can:

- understand a national park;
- discover activities;
- decide when to visit;
- plan their visit;
- understand permits, reservations, fees and access requirements;
- check current conditions;
- save useful trip research;
- identify what still requires official confirmation.

Readiness is one part of the wider trip-planning experience rather than the entire product.

---

## 5. Initial park coverage

Initial parks:

- Yosemite National Park;
- Rocky Mountain National Park;
- Yellowstone National Park;
- Zion National Park;
- Grand Canyon National Park.

Do not prioritize broad park coverage before these parks have reliable:

- source ingestion;
- data quality;
- navigation;
- weather;
- alerts;
- activities;
- access information;
- source attribution;
- update processes.

Expand to additional parks only when the core architecture and information quality are dependable.

---

## 6. Core user questions

The product should help a visitor quickly answer:

1. What can I do?
2. When should I go?
3. What must I arrange?
4. What permits, reservations or fees apply?
5. How do I get there and move around?
6. What facilities are available?
7. What conditions might disrupt my visit?
8. What information is current?
9. What still needs official confirmation?
10. Where can I verify this information?

Design pages around these questions rather than around the structure of the underlying APIs.

---

## 7. Primary park navigation

Each park should generally be organized around:

- Overview
- When to Visit
- Things to Do
- Plan Your Visit
- Conditions
- My Trip

Use progressive disclosure:

Show the most useful answer first.

Show supporting detail second.

Provide the official source alongside or near information where verification matters.

Do not overwhelm first-time users with every available field.

---

## 8. Park overview

Each park should provide:

- concise introduction;
- important highlights;
- key facts;
- real park imagery;
- orientation information;
- entrance information;
- major destinations;
- concise summaries with expandable detail;
- relevant source references.

The overview should help someone understand the park before requiring them to navigate numerous subpages.

---

## 9. Images and photo rights

Only use images when their reuse rights are verified.

For each externally sourced image, retain where practical:

- source;
- photographer/creator;
- title or description;
- source URL;
- rights/licence statement;
- attribution requirements;
- retrieval date.

Do not assume an image is reusable merely because it appears on a government website.

Verify relevant rights information.

If reuse rights are uncertain, do not publish the image.

Prefer official NPS imagery or other sources whose rights can be clearly established.

Images should use:
- responsive sizes;
- modern formats where appropriate;
- lazy loading;
- meaningful alt text;
- captions when useful;
- visible credits where required.

Optimize images so photo-led pages remain fast on mobile networks.

---

## 10. Things to do

Support park activities including where available:

- hikes;
- viewpoints;
- scenic areas;
- visitor attractions;
- ranger programs;
- tours;
- recreation;
- seasonal activities.

For each activity, preserve information such as:

- activity type;
- description;
- location;
- duration;
- season;
- accessibility;
- difficulty where officially supported;
- fees;
- permits;
- reservations;
- relevant restrictions;
- source;
- last checked time.

Do not invent attributes merely to make filtering complete.

If duration, accessibility, season or another attribute is unavailable, show that it is unavailable rather than fabricating a value.

---

## 11. Nearby recreation

Nearby recreation alternatives may be useful but must be clearly distinguished from places inside the national park.

Never make a nearby federal recreation area, private attraction, national forest location or other destination appear to be part of an NPS park when it is not.

Retain the responsible agency and geographic relationship.

---

## 12. Weather

Use National Weather Service information where appropriate for US park weather.

Forecasts must be tied to named locations.

Do not present one park-wide forecast when geography or elevation makes that misleading.

Examples may include:

- visitor centers;
- valleys;
- rims;
- major developed areas;
- important entrance regions.

Store enough metadata to identify:

- forecast location;
- coordinates or official grid reference where appropriate;
- forecast issue/update time;
- collection time;
- source;
- forecast period.

---

## 13. Forecast versus seasonal guidance

A weather forecast and seasonal climate guidance are different things.

Never make long-term seasonal information look like a forecast.

For dates inside the reliable forecast window:

Label information as a forecast.

For future dates beyond the forecast window:

Present clearly labelled seasonal or historical guidance where supported.

For example:

"Typical July conditions"

is acceptable if supported.

"Weather on July 17"

must not be presented as a forecast months in advance.

---

## 14. Weather alerts and park conditions

Support important information such as:

- official weather alerts;
- NPS alerts;
- closures;
- road restrictions;
- seasonal road access;
- trail or area restrictions where authoritative data exists;
- relevant transportation changes.

Always preserve:
- source;
- issue time where available;
- retrieval/check time;
- expiration where available;
- last successful refresh.

Display stale-data warnings when appropriate.

---

## 15. Safety language

Never declare:

- "Your trip is safe";
- "This park is safe";
- "There are no risks";
- "No alerts means conditions are safe."

Absence of a retrieved alert does not prove the absence of danger.

Use wording such as:

"No active alerts were retrieved from the monitored official sources as of [time]. Check official park information before travel."

Important safety-critical information should link users to the relevant official source.

The product helps people plan; it does not replace official guidance or personal judgment.

---

## 16. Visit planning

Provide useful planning information where supported, including:

- entrance fees;
- passes;
- timed-entry requirements;
- permits;
- reservations;
- operating hours;
- seasonal availability;
- entrances;
- roads;
- parking;
- shuttle systems;
- public transport information;
- campgrounds;
- visitor centers;
- toilets;
- drinking water;
- accessibility;
- pet rules;
- relevant facilities.

Show official booking or confirmation links when applicable.

Do not operate bookings or payments during the initial phase.

---

## 17. Reservations and permits

Reservation and permit requirements are high-priority information.

For each requirement, preserve where appropriate:

- what requires it;
- applicable dates;
- relevant location;
- source;
- booking authority;
- official booking link;
- last checked time.

Do not imply that the website itself confirms availability.

Distinguish:

"Reservation required"

from:

"Reservation currently available."

Unless real-time availability is explicitly supported and reliably integrated, direct users to the official booking platform for current availability.

---

## 18. Recreation.gov

Recreation.gov/RIDB may be used for appropriate federal recreation information where its data coverage and terms support the feature.

Do not assume Recreation.gov is authoritative for every NPS rule.

Where park-specific NPS guidance conflicts with generalized recreation data, investigate and prefer the source that is authoritative for the particular claim.

Preserve source identity.

---

## 19. Data source hierarchy

Prefer authoritative first-party sources.

Expected core sources include:

- National Park Service;
- National Weather Service;
- Recreation.gov/RIDB where appropriate.

Other datasets should be added only when:

- they answer a meaningful user question;
- source reliability is understood;
- reuse terms are acceptable;
- data can be maintained;
- conflicts can be handled safely.

Do not scrape random travel blogs to populate missing factual fields.

Editorial explanations may use broader reputable sources where appropriate, but operational facts should prioritize official sources.

---

## 20. Centralized data collection

Do not have every visitor's browser independently call NPS, NWS or Recreation.gov APIs.

Preferred architecture:

Official source
→ scheduled collection
→ validation
→ normalization
→ cached/current snapshot
→ website/API
→ visitor

This provides:

- predictable source usage;
- better performance;
- better resilience;
- consistent timestamps;
- stale-data detection;
- lower infrastructure cost;
- source auditability.

---

## 21. Different refresh schedules

Not all information needs the same refresh frequency.

Design refresh policies based on how rapidly information changes.

For example:

Higher frequency:
- active alerts;
- weather alerts;
- weather forecasts;
- closures;
- selected road/access conditions.

Lower frequency:
- park descriptions;
- activities;
- facilities;
- rules;
- accessibility information;
- image metadata.

Do not repeatedly request slow-changing information merely because another dataset requires frequent refresh.

Refresh frequency should respect source limits and reliability.

---

## 22. Data freshness

Retain at least these concepts where relevant:

1. Source reporting/issue time.
2. Retrieval/check time.
3. Publication/update time.
4. Last successful refresh.

Do not present retrieval time as if it were the source's issue time.

If a refresh fails, do not silently show old information as current.

Prefer:

"Last successfully updated at..."

and a visible stale-data indication when appropriate.

---

## 23. Failure handling

A source outage should not destroy previously valid production data.

Use safe publication patterns.

When refreshes fail:

- retain the latest known valid observation;
- mark its age;
- expose stale status where appropriate;
- record the failure;
- retry according to sensible rules;
- avoid publishing incomplete replacement data.

Never convert a failed API response into:

"No alerts"

or:

"Road open."

Unknown is not the same as clear/open/none.

---

## 24. Data state semantics

Keep distinct states such as:

- confirmed;
- unavailable;
- unknown;
- not applicable;
- source missing;
- stale;
- retrieval failed.

Do not replace unknown information with false, zero or empty values simply to make the interface look complete.

---

## 25. Personal trip tools

Initial personal trip functionality should be account-free.

Support:

- saved places;
- saved activities;
- itinerary;
- preparation checklist;
- unresolved requirements;
- important confirmations;
- printable trip summary;
- locally saved research.

Prefer browser storage such as:

- localStorage;
- IndexedDB

when technically appropriate.

Do not introduce user accounts simply to save trips.

Cloud accounts and synchronization belong to a later product phase.

---

## 26. Trip readiness

Readiness is a useful planning aid but must not become a simplistic "safe/not safe" score.

The trip tool may identify things such as:

- reservation not confirmed;
- permit requirement;
- seasonal road uncertainty;
- campground confirmation needed;
- weather should be rechecked;
- official alert should be reviewed.

Use concepts such as:

"Needs confirmation"

or:

"Check before travel"

rather than declaring a trip safe.

---

## 27. Print and trip summaries

Trip summaries should be useful offline and easy to understand.

Include where relevant:

- park;
- trip dates;
- selected activities;
- itinerary;
- reservation/permit checks;
- conditions check timestamp;
- important official links;
- unresolved requirements.

A saved/printed summary should state that conditions can change and official sources should be rechecked before travel.

---

## 28. Recommended architecture

Favor a low-cost, caching-heavy architecture.

Preferred direction:

- GitHub for source control;
- GitHub Actions and/or Cloudflare scheduled jobs for automated data collection;
- Cloudflare Workers + Static Assets for the public application;
- Cloudflare caching for frequently accessed current information;
- Cloudflare D1/KV where appropriate for small current-state and metadata needs;
- Cloudflare R2 where useful for archived source snapshots and larger retained artifacts;
- browser local storage/IndexedDB for initial personal trip data.

This is a preferred architecture, not an immutable constraint.

Change it when evidence demonstrates that another approach materially improves correctness, reliability, security or cost.

Do not introduce unnecessary:

- EC2 servers;
- RDS databases;
- Kubernetes;
- microservices;
- large data warehouses;
- complex queues;
- expensive managed systems

unless actual requirements justify them.

---

## 29. Cloud cost discipline

The project should target very low fixed infrastructure costs.

For the initial five parks, aim for approximately:

- minimal fixed infrastructure;
- CDN/static delivery for the majority of page content;
- centrally cached dynamic conditions;
- optimized imagery;
- no always-running traditional server where avoidable.

When technically sound alternatives exist, prefer:

- serverless;
- static delivery;
- caching;
- scheduled precomputation;
- object storage

over always-running infrastructure.

Before introducing meaningful recurring costs, explain:

- expected cost;
- reason;
- alternative approaches;
- what product requirement makes the cost necessary.

---

## 30. Mapping

The product needs useful orientation maps but is not initially a navigation application.

Maps may show:

- entrances;
- visitor centers;
- major destinations;
- parking areas;
- selected activity locations.

Do not build turn-by-turn navigation during the initial scope.

Prefer a technically and legally suitable low-cost map implementation.

Before adopting a commercial maps API with usage-based billing, compare:

- cost;
- licensing;
- caching restrictions;
- usage limits;
- open alternatives.

Do not assume maps must use Google Maps.

---

## 31. Search and SEO

Search discovery is important.

Create stable crawlable park pages with meaningful original utility.

Potential structure:

/
 /parks/
 /parks/yosemite/
 /parks/yosemite/things-to-do/
 /parks/yosemite/when-to-visit/
 /parks/yosemite/plan-your-visit/
 /parks/yosemite/conditions/

Equivalent structures may be used where they improve usability.

Use:

- descriptive titles;
- useful metadata;
- semantic HTML;
- internal linking;
- canonical URLs;
- structured navigation;
- sitemap;
- appropriate structured data where valid.

Do not create thousands of thin programmatic pages merely for search traffic.

A page should exist because it answers a useful visitor question.

---

## 32. Content quality and SEO

SEO must not produce generic filler.

Park content should be:

- specific;
- useful;
- source-backed where factual;
- easy to scan;
- clear about freshness;
- different enough across parks to provide genuine value.

Avoid producing large volumes of shallow AI-generated text.

Original analytical or organizational value should come from:

- combining useful official information;
- making requirements understandable;
- identifying unresolved trip checks;
- helping visitors navigate from an activity to access/weather/permit information.

---

## 33. Mobile-first usability

Many visitors will use the website during travel.

Mobile experience is therefore a core requirement.

Prioritize:

- fast loading;
- readable typography;
- touch-friendly controls;
- accessible filters;
- simple navigation;
- concise condition summaries;
- low-bandwidth behavior;
- usable offline/printed trip summaries.

Do not design only for large desktop dashboards.

---

## 34. Accessibility

Accessibility must be built in.

Use:

- semantic HTML;
- keyboard-operable controls;
- visible focus states;
- accessible form labels;
- meaningful image alt text;
- appropriate heading structure;
- sufficient contrast;
- text equivalents for important visual information.

Do not communicate an important state using color alone.

---

## 35. Performance

Park pages are image-heavy, so performance needs deliberate engineering.

Optimize:

- image dimensions;
- modern image formats;
- responsive images;
- lazy loading;
- caching;
- JavaScript bundle size;
- font loading;
- API payloads;
- repeated requests.

Do not send original multi-megabyte photos when a smaller responsive variant is appropriate.

Avoid unnecessary client-side libraries.

Important planning information should remain usable on slower mobile connections.

---

## 36. Data validation

Automated data refresh should include sensible validation.

Check where applicable:

- expected park identifiers;
- response structure changes;
- malformed data;
- duplicate records;
- missing required fields;
- timestamps;
- source failures;
- stale conditions;
- unexpected empty datasets;
- broken links;
- incorrect park mapping.

A failed validation should not silently publish corrupted production information.

---

## 37. Observability

The project should make it possible to determine:

- whether each source refresh succeeded;
- when it last succeeded;
- whether published data is stale;
- whether deployment succeeded;
- whether pages were generated correctly.

Prefer simple low-cost operational visibility first.

Do not introduce expensive enterprise monitoring unnecessarily.

---

## 38. Security

Treat this as a future public commercial product.

Apply secure engineering practices from the beginning.

Never:

- commit secrets;
- expose private API credentials client-side;
- trust arbitrary input;
- render unsanitized external content;
- expose unrestricted administrative endpoints;
- permit user-controlled URLs to cause unsafe backend requests.

Use appropriate:

- secrets management;
- least privilege;
- dependency scanning;
- secure headers;
- input validation;
- rate limiting when needed;
- CI/CD permissions;
- content sanitization.

---

## 39. Privacy

Initial architecture should minimize personal-data collection.

Since saved trips can initially live on the user's device, avoid creating accounts or storing unnecessary personal information.

If analytics, advertising, accounts, email or subscriptions are later introduced, reassess:

- privacy requirements;
- cookies;
- consent requirements;
- data retention;
- international visitors;
- applicable laws;
- third-party processing.

---

## 40. Monetization

The product may eventually use advertising and possibly additional paid features.

Do not prematurely introduce:

- ad networks;
- subscription billing;
- accounts;
- payment processing;
- commercial analytics;
- behavioral tracking

without explicit approval.

Build architecture that can support monetization later without making monetization the current engineering priority.

First establish:

- useful product;
- trustworthy information;
- reliable refresh;
- good search discoverability;
- strong user experience.

---

## 41. Later features

Potential later additions include:

- air quality;
- park comparisons;
- activity comparisons;
- transparent fee estimates;
- change-since-last-visit summaries;
- richer itinerary tools;
- alerts for saved trips;
- account synchronization.

Do not allow these features to distract from core data reliability.

---

## 42. Explicitly outside initial scope

Do not drift into:

- booking transactions;
- payment processing;
- guaranteeing campsite availability;
- guaranteeing parking availability;
- turn-by-turn navigation;
- unrestricted user reviews;
- declaring a trip safe;
- personalized medical advice;
- personalized legal advice;
- unsupported crowd predictions;
- unsupported hazard predictions.

---

## 43. Development priority

Follow this order unless repository evidence shows a prerequisite must be addressed first:

### Phase 1 — Foundations

1. Inspect and understand current repository.
2. Align project documentation with this revised scope.
3. Build reliable data ingestion.
4. Establish source provenance.
5. Implement caching and freshness tracking.
6. Implement safe failure/stale-state handling.
7. Establish clear page information architecture.

### Phase 2 — Core park experience

8. Build photo-led park overview pages.
9. Build When to Visit.
10. Build Things to Do.
11. Integrate named-location weather.
12. Integrate NWS alerts.
13. Integrate NPS alerts and changing conditions.
14. Display data freshness and official sources.

### Phase 3 — Detailed planning

15. Fees and passes.
16. Reservations and permits.
17. Entrances and transport.
18. Parking and shuttles.
19. Campgrounds.
20. Facilities.
21. Toilets and drinking water.
22. Accessibility.
23. Pet rules.
24. Useful visitor filters.

### Phase 4 — Personal trip tools

25. Saved places and activities.
26. Itinerary builder.
27. Preparation checklist.
28. Unresolved requirements.
29. Printable/saveable trip summary.

### Phase 5 — Expansion

30. Validate initial five-park experience.
31. Improve SEO/performance/accessibility.
32. Add new parks systematically.
33. Consider comparisons, air quality and other enhancements.
34. Consider accounts/alerts/monetization only when justified.

---

## 44. Priority hierarchy

Optimize decisions in this order:

1. Accuracy.
2. Source trust.
3. Safety of interpretation.
4. Data freshness.
5. Reliability.
6. Clear visitor guidance.
7. User experience.
8. Accessibility.
9. Performance.
10. SEO/discoverability.
11. Cost efficiency.
12. Broader park coverage.
13. Monetization features.

Never sacrifice factual reliability merely to make the site appear more complete.

---

## 45. Do not hide uncertainty

When data is:

- incomplete;
- stale;
- unavailable;
- conflicting;
- source-limited;
- awaiting confirmation

say so.

Examples:

"Not currently available from the monitored official source."

"Last successfully checked 3 hours ago."

"Seasonal road reopening date has not yet been confirmed."

"This activity may require a permit; verify current requirements with NPS."

Transparent uncertainty is preferable to false confidence.

---

## 46. Repository continuity

Maintain a durable project status/handover document.

A future ChatGPT/Codex session should be able to inspect the repository and quickly determine:

- current architecture;
- deployed URL/environment;
- implemented features;
- parks currently supported;
- sources in use;
- refresh frequencies;
- source limits;
- known data gaps;
- known stale-data issues;
- tests;
- deployment process;
- current milestone;
- blockers;
- next recommended task.

Update this document after substantial work.

Do not rely on the user to remember technical project history.

---

## 47. Architectural decisions

Record important architectural decisions when they materially affect future development.

Examples include:

- why a particular source was chosen;
- why a cache strategy exists;
- how stale weather is handled;
- how image rights are recorded;
- why a mapping provider was selected;
- why certain data is stored locally versus remotely.

Avoid undocumented technical decisions that future model sessions would need to rediscover.

---

## 48. When uncertain

If facing a technical problem:

1. inspect the existing implementation;
2. inspect tests and project documentation;
3. consult current authoritative technical/source documentation when necessary;
4. identify viable options;
5. choose the solution that best fits product requirements;
6. implement it;
7. test it;
8. document material decisions.

Do not ask the user to solve ordinary engineering questions.

Escalate to the user when uncertainty concerns:

- product intent;
- significant recurring cost;
- legal/data-rights risk;
- privacy;
- destructive actions;
- material external communication;
- major commercial commitments.

---

## 49. Core engineering principle

Treat National Park Explorer & Trip Planner as a real public product that may eventually receive substantial traffic and become commercially operated.

The user's lack of software-development involvement is not a reason to lower engineering standards.

It means ChatGPT/Codex must take greater responsibility for:

- architecture;
- implementation;
- testing;
- data reliability;
- deployments;
- operational resilience;
- security;
- cost control;
- documentation;
- project continuity.

The user should not need to become a software engineer in order for this product to be built and maintained correctly.

When reasonable technical decisions can be made from evidence, make them and proceed.

Build the product so another future ChatGPT/Codex session can understand it, operate it and continue development without depending on undocumented knowledge from previous conversations.
