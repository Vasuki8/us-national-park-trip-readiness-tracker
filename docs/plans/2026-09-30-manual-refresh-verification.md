# Manual refresh verification

The live five-park pilot publishes reviewed alert snapshots through deliberate updates. Public data can acquire later observations, omit old baselines from its bounded history, and have independently aged guidance and alert clocks. Development verification must accept those honest states while continuing to check the exact paired data and visitor limitations.

1. Correct informational copy that still describes public alerts/history and hosting as uncollected or pre-launch. Preserve manual collection, no continuous monitoring, stale/empty-feed limits, no indexing and no ads. Add generated-page regressions before changing the copy.
2. Replace launch-only observation/baseline counts with counts from the current paired histories in generated-site and browser checks. Verify exact clocks, metadata, omission labels and conditional baseline explanations using the existing mixed/truncated synthetic history fixtures. Retain successful public snapshots as a release requirement; degraded/uncollected fixtures verify truthful component rendering without clearing that requirement.
3. Use a reference clock after every non-null public evidence clock. Check each park's actual independent freshness at that clock, and use a guidance-specific clock when a browser scenario is deliberately testing reviewed annual guidance. Add synthetic regressions for an alert-only update after guidance expiry and nullable successful-feed clocks.
4. Run Node/Python tests, Astro check, both builds and generated-site checks; run supported browser verification if available. Review the complete diff and update the current handoff with measured results and remaining work.

This increment performs no real collection, data promotion, hosting change or deployment. The existing live artifact and original public evidence clocks remain the release baseline.
