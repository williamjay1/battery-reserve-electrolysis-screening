# Independent audit: native bound refinement and decision intervals

Audit phase: new computational results before manuscript integration.
Date: 2026-09-23. This is a read-only code/results audit. Only this note was
written. No solver outputs or analysis modules were changed by the auditor.

## Current computational decision

**GO for the refined reference bracket, its persisted dual certificate, the
independently replayed 60/300 s native lower schedules, and the completed
60/300/900 s coarse comparisons.** The certificate, targeted constraint
diagnostics and full one-minute computation are verified; see the addenda.
No computational audit item remains pending. This is a computational review
decision, not a manuscript acceptance or submission claim.

## Initial snapshot decision

**CONDITIONAL, with no mathematical blocker identified in the reference
bound/witness construction.** The reference native bracket is supported by
the relaxation direction and an independent full-sample physical replay.
Before describing the new bound as a reusable numerical certificate, save
the evaluated inequality multiplier and enough LP/support data to independently
recompute its value. Short-duration full coarse optima must be assessed from
their completed full-run files; the 60 s pilot is not a full-period result.

The bracket currently read is [502.790565720488, 502.811465704126] MWh.
Its width is 0.020899983638 MWh, or 0.0041566243% of the upper bound. The upper
bound is 5.888534295874 MWh below the 508.7 MWh comparator. This is an
optimization bracket, not a confidence interval and not an exact native optimum.

## Accepted mathematical components

1. **Relaxation direction is correct.** For an interval, the native increment
   F(b) is continuous, strictly increasing and concave: its slope decreases
   from 1/eta to eta when baseline passes an activation value. Thus its inverse
   g is convex. `supports` evaluates F at each admissible knot and obtains a
   valid inverse subgradient as the reciprocal of a one-sided derivative.
   At a charge/discharge kink the chosen right derivative of F yields a valid
   subgradient of g. Every tangent is a global lower plane for g.

2. **The assembled endpoint LP includes every physically feasible schedule.**
   Its constraints are F(BL) <= s[q+1]-s[q] <= F(BH), b[q] >= each inverse
   tangent at that increment, endpoint inventory in [0,E], and the same fixed
   initial and terminal E/2 inventory. The first-row shift by s0 has the correct
   sign. Native interior-prefix inventory constraints are omitted, so the
   feasible set expands. Minimizing sum(dt*b) therefore supplies a lower cost;
   subtracting it from S*T supplies an upper electrical-input allocation.

3. **Adaptive supports are legitimate.** The original endpoint knots remain
   the first two columns, preserving the interpretation used by
   `solve_endpoint`. New knots come from a bounded bisection of F at a relaxed
   endpoint increment and remain within [BL,BH]. Even if LP tolerance places
   that target slightly outside the endpoint range, the clipped endpoint knot
   still defines a valid global tangent. All earlier planes are retained.
   Monotone tightening of the theoretical relaxation follows; the observed
   evaluated upper sequence also decreases: 502.972584816, 502.844426701,
   502.816595274, 502.811465704 MWh for 17,18,19,20 supports respectively.

4. **Box residual compensation has the correct sign.** For min c'x with
   Ax<=d and l<=x<=u, any y<=0 gives a valid lower value
   d'y + l'max(r,0) + u'min(r,0), where r=c-A'y. This follows directly from
   y'Ax>=y'd and minimizing r'x over the box. The implementation clips the
   inequality marginals to nonpositive values and retains all finite lower
   and upper variable bounds. It does not substitute the primal objective
   for the dual bound.

5. **The coarse LP is exact for its stated model.** Its two additional affine
   planes are the two branches of the inverse constant-power increment map.
   Their maximum is the exact inverse. Positive dt objective coefficients
   make the baseline epigraph tight at the optimum. Coarse inventory is
   monotone within each constant-power interval, so endpoint inventory bounds
   suffice. The existing complete 900 s solution agrees with the earlier
   result: 512.856677825843 MWh, equation residual 1.11e-15 MWh and inventory
   replay violation 3.10e-13 MWh.

6. **The capacity-free scalar dual remains an evaluated upper bound.** The
   short-duration code uses seconds/3600 in baseline cost and 1/3600 for
   original samples. Sorting and quantile selection solve the separable
   baseline minimization. A nonzero aggregate inventory residual at an
   evaluated multiplier is not a physical schedule and does not invalidate
   its dual upper value. Omitting exact multiplier endpoints from the search
   can reduce tightness, but cannot reverse the bound direction. Do not call
   these evaluated values exact native optima.

7. **Algebraic backward reachability is consistent.** Reversing and negating
   activation, negating baseline, and replacing eta by 1/eta reverses every
   increment exactly. Reciprocal eta is used for an algebraic inverse map,
   not interpreted as a physical efficiency. Monotonicity in baseline
   remains valid for the backward interval construction. The 1e-7 MWh
   boundary guard is a translation of the interior inventory domain and
   preserves the physical initial and terminal E/2 after translation back.

## Independent physical replay actually performed

The auditor did not call `audit_schedule`. NumPy calculations independently
formed battery power .75*a-b, evaluated charge/discharge increments at every
one-second sample, accumulated inventories in 512-interval blocks, checked
all 18,313,200 samples, compared saved endpoint states, and computed the
electrolyzer allocation from sum((.1-b)*dt).

For `guided_witness_900s_round3_policy0.npz`:

- electrical input: 502.790565720531 MWh;
- terminal inventory residual: -5.13e-12 MWh;
- minimum/maximum inventory: 9.9994490e-8 / 1.999999899999857 MWh;
- maximum actual battery power magnitude: 0.905173277 MW;
- maximum abs(b)+R: 1.0 MW;
- electrolyzer input range: [0,0.35] MW;
- maximum discrepancy from saved endpoint states: 5.54e-12 MWh.

The full replay therefore passes physical inventory, actual battery power,
reserve headroom, electrolyzer load, initial/terminal and saved-state checks.
The independently calculated allocation differs from the serial saved audit
by 4.26e-11 MWh, consistent with accumulation order. Round-3 policy 1 also
passes; its lower allocation is 502.763382771426 MWh. The earlier round-1
examples pass a 1e-8 tolerance but include order-1e-11 nominal negative
inventories; the guarded round-3 policy-0 witness is the appropriate reference.

The production function `audit_schedule` checks all samples, inventory bounds,
abs(b)+R headroom, h in [0,1], and electrical allocation. Its callers check
the terminal condition separately. Under normalized activation in [-1,1],
the headroom condition implies the actual inverter limit. The independent
audit also checked the latter directly. No absent physical constraint was
found relative to the stated simplified model.

## Needs repair or explicit qualification

### R1 — Persist the new dual certificate (medium, reproducibility)

The inspected `upper_*.npz` files contain only states and baseline. The scalar
JSON reports alone cannot reconstruct d'y or stationarity residual correction
without rerunning the LP, because y is not retained. Persist the final y and
either the final support/LP data or a fully specified reconstruction record,
with hashes, bounds and objective coefficients. An independent recomputation
should agree with 5.888535295874142 MWh lower baseline cost and the resulting
502.811465704126 MWh upper allocation. This request has been sent to the owner.

### R2 — Qualify floating-point certification (required wording)

The implemented 1e-6 MWh outward margin is not interval arithmetic or a formal
rounding proof. The methods note correctly calls the result a floating-point
evaluated bound. Maintain that qualification. The round-3 LP primal has a
reported maximum inequality residual 8.73e-8, but this does not invalidate the
separately evaluated dual bound; nor is the relaxed primal used as a native
feasible schedule. The LP duality gap must not be substituted for the actual
native optimization bracket width.

### R3 — Extend the small-instance diagnostic (recommended)

All 12 reported small instances have nearly equal finite-capacity,
capacity-free and enumerated-optimum values after accounting for the fixed
1e-6 margin. They verify basic scaling and inequality direction, but provide
limited challenge to active capacity/prefix constraints. Add one or two
deliberately capacity- or prefix-active small examples, including a case
where the endpoint relaxation differs from the physical optimum or remains
feasible while the physical problem is infeasible. This is more informative
than increasing the number of similar nonbinding instances.

### R4 — Completed short-duration results only (required reporting)

At this audit snapshot, complete capacity-free bounds and native feasible
witnesses exist for 60 and 300 s, while the 60 s exact-coarse file is a
200-interval pilot. Native quick bounds are:

| Decision | New feasible lower (MWh) | Capacity-free evaluated upper (MWh) |
|---|---:|---:|
| 300 s | 499.813488936 | 507.007936835 |
| 60 s | 502.406078834 | 508.608373993 |

These are full 5,087 h computations with one-second physics. A repeated 900 s
schedule is also correctly inherited as a feasible shorter-duration schedule.
Retain the sample/interval counts and actual dt in reported comparisons.
Do not describe the full 60/300 s coarse optima as completed until their
full-run files and replay checks exist. The 60 s upper is only 0.091626 MWh
below the comparator, so its printed precision and conditional nature matter.

## Audited snapshot hashes

- `run_interval_bounds.py`: a5dceab83d50d3acefcd252abba0635a468d10bab6bab28729006b168f1ce95e
- `reachability.py`: 67b937703e0ea8e5254ca713964163b512528425075581fa76c273755974a2a7
- `audit_small_instances.py`: 2d4785b0c9c57923e1e6f1e96a53ecabc521d4c1283fd9b4b77f350dcade8ee1
- final reference witness: c93368bd74fa23f40a6ff2345d4dcaa65d7dd22a564c07c08b707d0f09abbf40

Later file changes or completed short-duration runs require only a focused
addendum for the affected items, not a repetition of this whole audit.

## Addendum: certificate and active constraints independently verified

The owner supplied `upper_900s_round3_dual_certificate.npz`, containing
inequality multipliers, knots, native endpoint values, inverse slopes, finite
box bounds, objective coefficients, primal variables and parameters. Its
SHA-256 is f61b9c0e6ea20952704f92f816aa6cecbe0befaa2fe915f8c31a4c3222c102e5.
**R1 is resolved.**

The auditor reconstructed A'y directly from adjacent-state coefficients
without calling the production LP assembly. With stored multipliers all
nonpositive, the independently evaluated quantities are:

- d'y = 8.744446293812596 MWh;
- box correction = -2.8559109979381163 MWh;
- corrected dual cost = 5.888535295874480 MWh;
- allocation upper = 502.811465704125570 MWh.

Differences from the saved certificate are below 3.2e-13 MWh. An independent
sorting/prefix-sum formula then recomputed every one of the 406,960 native
support evaluations from the original input. Maximum endpoint-value error
was 4.83e-15 MWh and maximum inverse-slope error was 9.37e-14. Stored finite
bounds and objective coefficients also matched the stated model.

The owner added `active_constraint_audit.json` with one endpoint-feasible but
physically prefix-infeasible case and two feasible capacity-active cases.
The seed, 48 candidate draws and selected input arrays are disclosed, so this
is an adversarial software diagnostic rather than a representative empirical
sample. A separately written sign-region enumeration using tighter 1e-9
primal/dual tolerances independently recovered:

| Fixture | Independent physical result |
|---|---:|
| Alternating +/-0.8, capacity 0.00005 MWh | Infeasible; zero feasible regions |
| Seed 3902309, draw 16 | 0.0003577779441718064 MWh; 2 feasible regions |
| Seed 3902309, draw 48 | 0.00035565625650327265 MWh; 3 feasible regions |

Both feasible values exactly match the recorded values at printed precision.
The finite-capacity upper improves on the capacity-free upper by 3.5662e-6
and 5.8470e-7 MWh. **R3 is resolved.** This closes the substantive reference
computation audit; the floating-point qualification in R2 remains appropriate.

## Addendum: exact network formulation of the coarse model

`coarse_network.py` is mathematically equivalent to the interval-constant
coarse LP, not an additional native relaxation. Let u denote R times mean
activation and w the inventory increment. The inverse map is

    b = u + w+/(eta*dt) - eta*w-/dt,

where w+ = max(w,0), w- = max(-w,0). Cyclic inventory implies sum(w+) =
sum(w-), hence

    sum(b*dt) = sum(u*dt) + (1/eta-eta)*sum(w+).

Minimizing positive inventory flow therefore minimizes the original charging
cost at eta=0.94. The implemented positive-flow bounds are
[max(F(BL),0), max(F(BH),0)] and negative-flow bounds are
[max(-F(BH),0), max(-F(BL),0)]. If either increment endpoint forces a sign,
the opposite flow has upper bound zero. If both flows can be positive, both
have zero lower bounds; reducing them together preserves inventory and
strictly reduces the positive-flow objective. Consequently an optimum has
no simultaneous flows and maps back to a physical coarse baseline. Inventory
equalities and the fixed terminal state are assembled with the correct signs.
Unrestricted equality multipliers and box residual compensation give the
appropriate evaluated dual lower cost.

The complete 900 s network result reproduces 512.856677825843 MWh exactly at
printed precision. The complete 300 s result has 61,044 intervals and objective
510.199727168889 MWh, zero simultaneous flow, maximum replay violation
1.78e-15 MWh, and corrected primal/dual cost gap 2.31e-14 MWh. The full
60 s result must contain 305,220 intervals; its then-pending output should
be checked before delivery. No pilot may be substituted.

## Addendum: main-body and assembly claim mapping

The draft screen inequality, primal/dual enclosure directions, distinction
between capacity-free and finite-capacity targets, throughput lower-bound
calculation, and interpretation of German monthly outcomes are supported.
The GB rewrite matches `gb_transfer_audit.json`: six months have positive
signed energy; May alone has imports 0.038886458 MWh, a positive-gain
throughput threshold 0.629265747 MWh and an upper-implied throughput minimum
149.095388281 MWh. The text correctly distinguishes five feasible coarse
loss cases from April/June infeasibility and avoids a national market claim.

Two wording repairs and one input-file mapping repair were sent to the lead:

1. Replace “selected lower-quantile windows show the same loss direction” by
   an explicit positive coarse-minus-native discrepancy statement. The P99
   window has native net charging +0.002353 MWh and coarse +0.005613 MWh;
   it is not a native net-energy loss despite its positive discrepancy.
2. Replace “Endpoint, maximum and mean summaries” with “Minimum, maximum and
   mean summaries”.
3. Let `assemble_revision.py` read completed `*_coarse_network.json` as well
   as the earlier `*_coarse.json` filenames. Otherwise a completed network
   solution incorrectly remains pending in the table.

These points do not invalidate the new mathematical or empirical result.

## Addendum: improved short-duration witnesses independently replayed

The owner subsequently supplied capacity-free-guided, physically repaired
native schedules for 60 and 300 s decisions. The auditor again replayed all
18,313,200 original seconds with independent NumPy code, not the production
audit, and directly verified the throughput identity.

| Decision | Intervals | Independent H (MWh) | Terminal residual (MWh) | Maximum saved-state difference (MWh) |
|---|---:|---:|---:|---:|
| 60 s | 305,220 | 506.662051774923 | +3.69e-12 | 3.81e-12 |
| 300 s | 61,044 | 504.883759372021 | -1.33e-11 | 1.38e-11 |

Both have inventory within approximately [1e-7,1.9999999] MWh, actual inverter
power and full reserve headroom at most 1 MW, and electrolyzer input within
[0,0.35] MW. Throughput-identity residuals are at most 1.21e-12 MWh. Differences
from the serial reported objectives are below 2.6e-10 MWh. Thus the documented
small projection of feasibility-query coordinates does not conceal a physical
inventory violation in the stored schedules. These stronger lower bounds
supersede the earlier quick witnesses for the main comparison, while the
earlier candidates remain valid and retained.

## Final addendum: full one-minute coarse completion and executable audit

The complete one-minute network LP has now finished with 305,220 intervals.
Independent replay gives 508.930290352224 MWh, 0.230290352224 MWh above the
508.7 MWh comparator. Maximum equation error is 3.47e-18 MWh and terminal
inventory error is 1.60e-14 MWh. Inventory spans [0.037110162571,2+6e-15] MWh;
baseline bound excursions are at most 7.2e-15 MW. The network cost identity
differs by only 3.55e-14 MWh. Full 5- and 15-minute coarse solutions were also
independently replayed: 510.199727168889 and 512.856677825843 MWh. Thus all
three tested durations have a feasible coarse gain and native evaluated
upper below their common comparator, within the stated model.

The entire independent check is saved as the portable script
`analysis/independent_interval_recheck.py`, with machine-readable result
`results/independent_interval_recheck.json`. The actual run is **PASS** for
406,960 native supports, the stored dual certificate, three complete native
physical replays, three complete coarse replays, and three targeted synthetic
fixtures. It imports no production analysis modules and solves no large LP.
Its default source is `prepared_inputs/native_evaluation.npy`; use
`--native-input PATH` or `SCREEN_NATIVE_INPUT` for an authorized external cache.
Only the small sign-region diagnostic LPs are independently solved.
