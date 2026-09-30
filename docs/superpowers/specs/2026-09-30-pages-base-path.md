# GitHub project Pages support

The pilot must work at `/` and `/us-national-park-trip-readiness-tracker/` so free GitHub project hosting is possible without a custom domain. All internal page links, scripts and styles must stay under the selected path; external NPS links and fragment links retain their destinations. Active navigation must identify the current page under either path.

CI must build and verify both outputs from the same commit and public data, retaining `dist/` and `dist-pages/` in the existing verification artifact. Each build manifest records its base path. Verification covers all internal HTML destinations/assets and project-path browser navigation, search, entry guidance and checklist behavior.

Manual release and rollback select an already verified output whose manifest path matches `configure-pages` metadata. A missing or mismatched output fails before upload. Earlier artifacts without a base-path field can only be used for root hosting. No rebuilding during release, automatic deployment, private-data publication, indexing or advertising changes.
