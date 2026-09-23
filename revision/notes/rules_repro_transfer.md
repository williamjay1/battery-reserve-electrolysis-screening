# Rule, reproduction, and input-transfer audit

**Audit date:** 23 September 2026.  This note separates a market-rule claim
from a modeling choice, records the public-reproduction boundary, and gives
the numerical basis for the Great Britain (GB) transfer wording.  It does not
alter the manuscript and does not treat the GB transformation as reserve
dispatch data.

## 1. German aFRR time layers

### What the primary sources support

1. The German TSOs' market overview states that **balancing-energy market
   products last 15 minutes**, with a market for each quarter-hour product
   closing 25 minutes before its start.  It separately says that aFRR/mFRR
   balancing-energy needs are sent to call-off platforms **in real time**.
   This is a product/bid-validity fact, not a rule fixing physical power or a
   battery recovery baseline for 15 minutes.

   - German TSOs (50Hertz, Amprion, TenneT, TransnetBW), *How does the
     balancing market work?*, Regelleistung, accessed 2026-09-23.
     <https://www.regelleistung.net/en-us/General-Information/How-does-the-balancing-market-work>

2. The German aFRR settlement page says that the tolerance band is placed
   around the **load-frequency-controller setpoint** and measured in seconds;
   underperformance is evaluated over second intervals in a rolling five-minute
   window.  It therefore supports replaying a second-resolution setpoint and
   contradicts a claim that a 15-minute product implies a 15-minute constant
   activation trajectory.

   - German TSOs, *Settlement: automatic Frequency Restoration Reserve*,
     Regelleistung, accessed 2026-09-23.
     <https://www.regelleistung.net/en-us/Become-a-balancing-service-provider/Settlement/automatic-Frequency-Restoration-Reserve>

3. The German TSO settlement-model reading version explicitly defines the
   aFRR accounting interval as one second; its inputs are aFRR setpoint and
   actual MW values, and its calculations use second-level power values.  It
   also makes an important reporting distinction: **PT15M power values are
   means of the respective quarter-hour** (Appendix A, p. 22).  Thus a
   quarter-hour settlement/reporting file is not evidence that either the
   controller setpoint or an asset's recovery baseline is piecewise constant.

   - German TSOs, *Modellbeschreibung Abrechnung der aFRR-Arbeit*, dated
     26 November 2021, current online reading version accessed 2026-09-23,
     pp. 3, 9, 20--22.
     <https://www.regelleistung.net/cdn/files/d7577652-1d73-46cd-6f96-08ded04f7ece/modellbeschreibung_afrr-abrechnung_ab_01.10.2021-30.08.2026.pdf>

4. The ENTSO-E-hosted all-TSO aFRR implementation document corroborates the
   separation: the standard bid has a **15-minute validity period**, is
   automatically activated, and can be activated or deactivated at any time
   during that validity period; the document sets a five-minute full-activation
   time.  This supports the terminology distinction but should be cited as an
   ENTSO-E-hosted implementation document, not as evidence that the paper's
   battery baseline is mandated by German rules.

   - All TSOs, *Implementation framework for the European platform for the
     exchange of balancing energy from frequency restoration reserves with
     automatic activation*, under Article 21 of Commission Regulation (EU)
     2017/2195, ENTSO-E, published 2 February 2024, accessed 2026-09-23.
     <https://eepublicdownloads.entsoe.eu/clean-documents/nc-tasks/240131_Art%2021_EB%20Regulation_allTSOamendment%20aFRR-IF%20-%20Annex%20I_tracked%20changes_final.pdf>

### Safe manuscript wording

> We choose a 15-minute piecewise-constant recovery baseline as a modeling
> decision interval at the same scale as the aFRR balancing-energy product.
> It is not treated as a German operational requirement.  The activation input
> is replayed at one-second resolution: the market-rule sources distinguish a
> 15-minute bid-validity/product horizon from automatic real-time activation
> and second-level settlement.

Avoid wording such as “German aFRR rules require the baseline to be fixed for
15 minutes” or “15-minute settlement means that aFRR control is constant for
15 minutes.”

## 2. Existing German reconstruction evidence and its boundary

The current local staging repository at
`D:\MLWork\06\Applied_Sciences_energy_revision_20260923\public_repository`
already contains the following evidence:

- `provenance/GERMAN_RECONSTRUCTION.md` names the Version 1 source snapshot
  (Zenodo `10.5281/zenodo.22659529`, commit
  `36aeb2a08dd7682e4f210c7718b188bb4c67cac3`) and the three historical
  executable paths: `download_germany.py`, `cache_germany.py`, and
  `prepare_evaluation_cache.py`.
- `provenance/germany_raw_files.json` contains the 19-file January 2025--July
  2026 inventory, byte sizes, and SHA-256 values.  The documented target
  cache has SHA-256
  `0a664312a5bdbb5b7bf3b12dc8e203c932f1b07b7e029abf887e9599efc91163`,
  18,313,200 samples, 20,348 full quarters, and 5,087 hours.
- `provenance/DATA_SOURCES.md` states the provider and licensing boundary;
  `data/PREPARED_INPUTS.md`, `REPRODUCTION.md`, and
  `RUN_REVISION_EVIDENCE.md` describe the required local cache layout.
- The portable model/result code exists in `src/`, including
  `revision_evidence.py`, `reachability.py`, `hydrogen_lp_pilot.py`,
  `native_hydrogen_bound.py`, `cyclic_energy_dual.py`,
  `verify_hydrogen_optimization.py`, and `main_result_audit.py`.  The staged
  tree has `MANIFEST.json` and `SHA256SUMS.txt`; original code and docs are
  MIT-licensed, while third-party data remain under provider terms.

What is deliberately **not** in Version 2 is equally important:

- No raw German records, daily cache, or `native_evaluation.npy` cache is
  redistributed.
- The actual downloader/parser/cache scripts are referenced in the Version 1
  snapshot but are not present as executable files in the Version 2 staging
  tree.  The Version 2 repository therefore documents a reconstruction route;
  it is not by itself an end-to-end German downloader bundle.
- `src/revision_evidence.py` needs authorized `prepared_inputs/`, including
  German and GB-derived files.  A reviewer without those materials cannot run
  the central empirical pipeline from Version 2 alone.

## 3. GB transfer: evidence-based reason the German reversal does not recur

The following values were recomputed read-only from the seven local files in
`prepared_inputs/gb_frequency/` using the deposited
`src/hydrogen_lp_pilot.py` and `src/cyclic_energy_dual.py`, with
`E=2` MWh, `S=0.1` MW, `R=0.75` MW, `eta=0.94`, 15-minute decisions, and the
same cyclic convention.  The GB arrays are the stated frequency-to-activation
transformation, **not observed aFRR instructions**.

| Month | Signed reserve energy $\mathcal{U}$ (MWh) | Native capacity-free evaluated upper minus $H_0$ (MWh) | Quarter model |
|---|---:|---:|---|
| Jan | +2.153 | -10.422 | feasible; exact value is -8.218 MWh below $H_0$ |
| Feb | +0.361 | -8.164 | feasible; -6.193 below $H_0$ |
| Mar | +1.207 | -9.841 | feasible; -7.593 below $H_0$ |
| Apr | +1.962 | -10.779 | **infeasible** under the stated cyclic quarter-fixed constraints |
| May | -0.039 | -9.175 | feasible; -6.872 below $H_0$ |
| Jun | +1.651 | -11.014 | **infeasible** under the stated cyclic quarter-fixed constraints |
| Jul | +0.746 | -8.905 | feasible; -6.640 below $H_0$ |

The mechanism follows the paper's exact cyclic identity,

$$H-H_0=-\mathcal{U}-\kappa\mathcal{Q},\qquad
\kappa=(1-\eta^2)/(1+\eta^2)=0.06179656.$$

For January--April, June, and July, $\mathcal{U}>0$, so any cyclic feasible
schedule has $H-H_0<0$ even before loss-relevant throughput is considered.
May is the only monthly GB record with a negative signed energy, but it is only
-0.0389 MWh: a gain would require $\mathcal{Q}<0.629$ MWh.  Its native upper
bound instead implies $\mathcal{Q}\ge149.095$ MWh, so conversion losses
overwhelm that very small import.  This is a quantitative reason for the
non-recurrence, rather than an unsupported country-level speculation.

The GB paragraph should therefore say:

> The capacity-free native evaluated upper value is below the no-reserve
> comparator in every GB month.  The quarter-mean model is also below the
> comparator in the five cyclically feasible months (January, February, March,
> May, and July); April and June are infeasible under the stated
> quarter-fixed, cyclic constraints.  Six months have nonnegative signed
> reserve energy, which alone rules out a gain under the cyclic identity; the
> remaining May case has imports far too small relative to the throughput
> implied by the native upper bound.  These are properties of the specified
> frequency-derived input, not a comparison of national aFRR markets.
