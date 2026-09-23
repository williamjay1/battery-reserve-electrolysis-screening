# Public release checklist

Complete these steps only when the author is ready to make a public data/code release.

1. Review every file in the staged Git tree. Confirm that no manuscript PDF, raw German aFRR record, local path, credential, or personal data is present.
2. Preserve the Version 2 boundary: do not publish German native aFRR records or the German source-derived `native_evaluation.npy` cache. Verify the upstream terms before reconsidering that decision for any future release.
3. If a future prepared-input bundle is permitted, generate a SHA-256 manifest and test extraction into a clean directory. Run `python src/revision_evidence.py` from that directory and compare the new manifest with the tracked results.
4. Update the staged package version and release date in `CITATION.cff`; update `.zenodo.json` if the release description or author metadata changes.
5. Create a public GitHub repository and push the staged files. Keep `prepared_inputs/` out of Git; use a release asset only when Step 2 permits it.
6. Create a GitHub Release with a specific tag and a concise description of the repository contents. Attach any permitted prepared-input bundle and its checksum manifest.
7. Confirm that the GitHub–Zenodo integration has created a public Zenodo record for that exact release. Record the concept DOI and version DOI separately if Zenodo provides both.
8. Only after verification, insert the exact version DOI in the manuscript's Data Availability Statement and archive the release URL in the submission records.

Do not cite `10.5281/zenodo.22659529` as the DOI of this revision: it belongs to an earlier archive.
