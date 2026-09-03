# Anonymous-submission and artifact plan

This document prepares the project for a possible double-blind IASEAI'27 submission. The official 2027 anonymity/artifact instructions must still be re-checked when the submission guide is published; this plan does not assume that the 2026 policy is unchanged.

## Submission principle

The anonymous manuscript must not reveal author identity through repository links, usernames, local paths, PDF metadata, acknowledgements, artifact URLs, commit authorship, or supplementary-file metadata. The public development repository is useful for research engineering, but it should not automatically be linked from a double-blind submission.

Because the development repository is public and contains normal Git authorship/history, a reviewer who searches for the exact project may be able to discover author identity. Before submission, explicitly decide repository visibility and artifact-sharing strategy based on the official IASEAI'27 rules. Do not rely on the absence of a hyperlink in the PDF as a complete anonymity guarantee.

## Anonymous artifact package

`scripts/package_anonymous_artifact.py` creates a sanitized source archive intended for review-time supplementary use if anonymous artifacts are permitted. It deliberately excludes:

- `.git/` and all Git history/author metadata;
- `.github/` workflow metadata;
- the development `README.md` and `CITATION.cff`;
- local runbooks/progress files that name the development repository;
- API keys, `.env` files, local environment snapshots, and provider billing exports;
- downloaded ImperfectiveNLI bytes;
- raw/processed model outputs and result archives;
- generated local artifacts and caches.

The package contains the scientific source/configuration, analysis scripts, tests, data provenance metadata, dependency files, and an automatically generated anonymous README. The packager scans selected text files for known project-account identifiers and refuses to create the archive if any are present.

The anonymous package is a review artifact only. It does not replace the exact frozen Git commit and raw evidence archive used for final reproducibility.

## Before submission

1. Re-check the official IASEAI'27 anonymity, supplementary-material, and artifact-linking policy.
2. Remove or anonymize author names, affiliations, acknowledgements, grant identifiers, personal URLs, ORCIDs, repository usernames, and identifying PDF metadata from the submission package.
3. Do not link the public development repository from a double-blind manuscript unless the venue explicitly permits deanonymized artifacts.
4. If an anonymous supplement is allowed, build it from the exact scientific freeze and inspect the ZIP manually after the automated scan.
5. Verify that filenames, archive metadata, generated README text, logs, and example shell paths do not reveal identity.
6. Keep the real development repository, raw outputs, and final archival artifact separate from the anonymous review package.
7. After acceptance or when anonymity is no longer required, publish the full attribution/provenance information and the exact submission snapshot according to the venue policy.

## Scientific integrity

Anonymization must never alter scientific settings, data labels, prompts, model identifiers, thresholds, metrics, or analysis code. If a file cannot be anonymized without changing the experiment, omit it from the review artifact and document the omission rather than silently modifying the scientific record.
