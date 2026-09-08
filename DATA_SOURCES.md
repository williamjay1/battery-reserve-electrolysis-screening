# Data sources and rights

Checked 8 September 2026 against the official provider pages.

| Source | Coverage and transformation | Release contents | Terms |
|---|---|---|---|
| German TSOs, Netztransparenz aFRR setpoints | January 2025 to July 2026, 577 complete local days; native seconds, DST-aware parsing; model normalization and clipping described in code | Source-file list, hashes, daily-cache hashes, quality audit, acquisition/parsing code and analytical results. Native records and lossless German caches excluded | https://www.netztransparenz.de/de-de/Impressum reserves reproduction rights except legally permitted use; no separate redistribution grant established |
| Elia ODS127 | Validated quarter-hour volumes; 574 complete UTC days over the same span; engineering driver, not individual delivery | Derived quarter caches and processing code | https://opendata.elia.be/pages/licence/ : CC BY 4.0, provider's stated Belgian-law terms |
| National Energy System Operator, GB frequency | January to July 2026; frequency transformed to activation = clip((50-f)/0.2,-1,1); complete 900-second quarters | Seven derived activation/timestamp caches and processing code | https://www.neso.energy/data-portal/neso-open-licence |

Sources:
- https://www.netztransparenz.de/en/Balancing-Capacity/Balancing-Capacity-data/Data-in-second-resolution
- https://opendata.elia.be/explore/dataset/ods127/
- https://www.neso.energy/data-portal/system-frequency-data

Elia attribution: source Elia Open Data, derived from ODS127 validated system records; transformed/filtered by Junjie Zhang. These are not unmodified source exports.

NESO attribution: **Supported by National Energy SO Open Data.** Frequency is observed; derived activation is a modelling transformation, not an observed battery instruction. NESO does not endorse this study. Provider rights remain applicable to derived caches.

German source providers: 50Hertz Transmission, Amprion, TenneT TSO and TransnetBW via Netztransparenz. Exclusion from this public release is not a claim that public source access is unavailable. Full reconstruction requires obtaining the monthly source ZIPs from the provider. The monthly filenames and SHA256 are recorded in provenance/germany_raw_files.json. Existing private raw files on E remain unchanged.

Author-created code, documentation and analytical results are released under CC BY 4.0. Third-party material retains its own license; this archive does not grant rights the author does not hold.
