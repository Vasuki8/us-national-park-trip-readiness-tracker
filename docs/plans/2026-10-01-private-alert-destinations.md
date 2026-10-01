# Private alert destinations and unchanged live-region results

Continue the existing reviewed development branch with two bounded repairs before further operator collection work.

1. Make the alert archive API, staging API and offline archive CLI require an explicit absolute, traversal-free destination outside the entire checkout and its ancestors. Reuse one shared destination guard, reject raw traversal/symlink ancestry, then compare canonical containment before archive access, staging writes or provider requests. Test the formerly allowed ignored/unlisted checkout folders as well as relative, ancestor and Linux doubled-leading-slash aliases, using synthetic inputs without writes to the checkout.
2. Replace stale relative/in-checkout examples in the active staging/archive runbooks with external absolute paths. Retained old stores are not moved, read, deleted or repaired automatically. Existing permission and backup responsibilities remain separate.
3. Avoid unchanged trip-result text mutations during minute/visibility refreshes. Execute the real script with synthetic inputs to reproduce redundant updates and verify that the seven-day stale transition still changes the result.
4. Run the full Node/Python suites, Astro check, both builds and generated-site checks; obtain supported-Linux browser CI and independent review. Update PR #5 around the final scope and record the current handoff.

These repairs do not collect real sources, promote public data, merge, deploy, schedule, enable indexing or add ads.

Completed: implementation `cddc650eaa28099510ce56dd7eda9857f85e7836` passed [Verify pilot #171](https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/actions/runs/36816421519), with 206 Node, 419 Python, 44 generated-site and 81 Chromium tests (750 total), both 14-page builds and all three retained accessibility screenshots. Local strict TypeScript and independent review also passed. PR #5 contains this repair and the preceding manual-refresh verification/copy work; integration and release remain deliberate next actions.
